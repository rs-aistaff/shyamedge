import time
import sys
from datetime import datetime, timedelta, time as dtime
from typing import Optional, Dict, Any
import zoneinfo

from config.settings import settings
from config.trading_hours import MarketSessionManager, IST_TZ
from core.constants import Underlying, StrategyID, OptionType, SignalDirection, LOT_SIZES
from core.models import Bar, Position, Trade, Signal
from indicators import (
    IntradayVWAP, StreamingEMA, StreamingRSI, StreamingATR,
    OpeningRangeTracker, KeyLevelsTracker
)
from regime_detector import MarketRegimeDetector
from strategies import (
    ORBStrategy, VWAPEMAStrategy, PullbackContinuationStrategy,
    BreakoutVolumeStrategy, DonchianBreakoutStrategy,
    PivotReversalStrategy, GapContinuationStrategy
)
from option_engine import OptionStrikeSelector, OptionValidator
from data_engine import OptionPricingEngine
from risk_engine import VirtualPortfolio, RiskLimitsValidator, KillSwitchManager
from broker import PaperBroker
from alerts import TelegramAlertService
from database.connection import init_db
from database.repository import Repository

class LiveMarketDaemon:
    """
    Automated Morning Live Market Paper Trading Daemon.
    Synchronizes strictly with IST market sessions:
    - 09:00 - 09:15: Pre-market status, daily reset, health checks
    - 09:15 - 09:30: Opening Range (ORB) capture
    - 09:30 - 14:30: Active multi-strategy scanning on every 5-min bar close
    - 14:30 - 15:15: Cutoff (position management & trailing stops only)
    - 15:15 - 15:30: Mandatory square-off
    - 15:30+: End-of-day reporting & Telegram summary
    """
    def __init__(self, underlying: Underlying = Underlying.SENSEX, is_simulation: bool = False):
        self.underlying = underlying
        self.is_simulation = is_simulation
        self.is_running = True

        init_db()
        self.portfolio = VirtualPortfolio(
            initial_capital=settings.initial_capital,
            max_daily_loss_pct=settings.max_daily_loss_pct
        )
        self.broker = PaperBroker(
            portfolio=self.portfolio,
            slippage_pct=settings.default_slippage_pct
        )
        self.risk_validator = RiskLimitsValidator(
            portfolio=self.portfolio,
            kill_switch_active=KillSwitchManager.is_active()
        )

        # Core Alpha Strategies
        self.strat_donchian = DonchianBreakoutStrategy()
        self.strat_breakout_vol = BreakoutVolumeStrategy()
        self.strat_pivot = PivotReversalStrategy()
        self.strat_gap = GapContinuationStrategy()
        self.strat_orb = ORBStrategy()
        self.strat_vwap_ema = VWAPEMAStrategy()
        self.strat_pullback = PullbackContinuationStrategy()

        # Quantitative math trackers
        self.vwap_calc = IntradayVWAP()
        self.ema_20_calc = StreamingEMA(period=20)
        self.ema_50_calc = StreamingEMA(period=50)
        self.rsi_calc = StreamingRSI(period=14)
        self.atr_calc = StreamingATR(period=14)
        self.or_tracker = OpeningRangeTracker()
        self.levels_tracker = KeyLevelsTracker(swing_period=20)
        self.regime_detector = MarketRegimeDetector()

        self.volume_history = []
        self.atr_history = []
        self.highs_history = []
        self.lows_history = []
        self.day_open_price: Optional[float] = None
        self.first_15m_high: Optional[float] = None
        self.first_15m_low: Optional[float] = None
        self.prev_bar: Optional[Bar] = None
        self.ema_20_prev: Optional[float] = None
        self.latest_bar: Optional[Bar] = None

    def get_session_phase(self, current_dt: datetime) -> str:
        current_time = current_dt.time()
        if current_time < dtime(9, 15):
            return "PRE_MARKET"
        elif dtime(9, 15) <= current_time < dtime(9, 30):
            return "OPENING_RANGE"
        elif dtime(9, 30) <= current_time < dtime(14, 30):
            return "ACTIVE_TRADING"
        elif dtime(14, 30) <= current_time < dtime(15, 15):
            return "CUTOFF_MANAGEMENT"
        elif dtime(15, 15) <= current_time < dtime(15, 30):
            return "SQUARE_OFF"
        else:
            return "MARKET_CLOSED"

    def render_live_telemetry(self, current_dt: datetime, candle_countdown_sec: int):
        phase = self.get_session_phase(current_dt)
        phase_colors = {
            "PRE_MARKET": "\033[93m",        # Yellow
            "OPENING_RANGE": "\033[96m",     # Cyan
            "ACTIVE_TRADING": "\033[92m",    # Green
            "CUTOFF_MANAGEMENT": "\033[93m", # Yellow
            "SQUARE_OFF": "\033[91m",        # Red
            "MARKET_CLOSED": "\033[90m"      # Grey
        }
        color = phase_colors.get(phase, "\033[0m")
        reset = "\033[0m"

        pos = self.portfolio.active_position
        pos_str = "None (Flat)"
        unrealized = 0.0

        if pos and self.latest_bar:
            cur_prem = OptionPricingEngine.estimate_premium(
                spot=self.latest_bar.close, strike=pos.strike,
                option_type=pos.option_type, expiry=pos.expiry, current_dt=current_dt
            )
            unrealized = (cur_prem - pos.entry_price) * pos.quantity
            pos_str = f"{pos.option_symbol} | Entry: ₹{pos.entry_price:.2f} | Cur: ₹{cur_prem:.2f} | PnL: ₹{unrealized:+.2f}"

        # Clean single-line live telemetry output
        time_str = current_dt.strftime("%H:%M:%S IST")
        regime_str = self.latest_bar.regime.value if self.latest_bar and self.latest_bar.regime else "INITIALIZING"
        ltp_str = f"₹{self.latest_bar.close:.2f}" if self.latest_bar else "N/A"

        total_pnl = self.portfolio.daily_realized_pnl + unrealized
        account_equity = self.portfolio.current_capital + unrealized

        status_line = (
            f"[{time_str}] {color}[{phase:<17}]{reset} "
            f"LTP: {ltp_str:<9} | "
            f"Active: {pos_str} | "
            f"Running MTM: ₹{unrealized:+7.2f} | "
            f"Closed PnL: ₹{self.portfolio.daily_realized_pnl:+7.2f} | "
            f"Total PnL: ₹{total_pnl:+7.2f} | "
            f"Next Bar: {candle_countdown_sec:02d}s"
        )
        sys.stdout.write(f"\r{status_line}")
        sys.stdout.flush()

    def on_candle_close(self, bar: Bar) -> Dict[str, Any]:
        """Called whenever a 5-minute candle completes."""
        self.latest_bar = bar

        # 1. Update Indicators
        bar.vwap = self.vwap_calc.update(bar.timestamp, bar.high, bar.low, bar.close, float(bar.volume))
        bar.ema_20 = self.ema_20_calc.update(bar.close)
        bar.ema_50 = self.ema_50_calc.update(bar.close)
        bar.rsi_14 = self.rsi_calc.update(bar.close)
        bar.atr_14 = self.atr_calc.update(bar.high, bar.low, bar.close)

        or_h, or_l, is_or_ready = self.or_tracker.update(bar)
        swing_h, swing_l = self.levels_tracker.update(bar.high, bar.low)

        self.volume_history.append(bar.volume)
        if len(self.volume_history) > 20: self.volume_history.pop(0)
        avg_vol = sum(self.volume_history) / len(self.volume_history)

        self.atr_history.append(bar.atr_14)
        if len(self.atr_history) > 20: self.atr_history.pop(0)
        avg_atr = sum(self.atr_history) / len(self.atr_history)

        # 2. Market Regime
        regime = self.regime_detector.detect(bar, ema_20_prev=self.ema_20_prev)
        bar.regime = regime

        # 3. Position Management (Stop Loss / Target / Square-off)
        pos = self.portfolio.active_position
        if pos:
            cur_prem = OptionPricingEngine.estimate_premium(
                spot=bar.close, strike=pos.strike, option_type=pos.option_type,
                expiry=pos.expiry, current_dt=bar.timestamp
            )
            pos.current_price = cur_prem
            pos.unrealized_pnl = round((cur_prem - pos.entry_price) * pos.quantity, 2)
            Repository.save_or_update_position(pos)

            # Universal Trailing Stop & Profit Lock Management
            gain_pct = (cur_prem - pos.entry_price) / pos.entry_price

            # Rule 1: Fast Breakeven Lock at +8% gain (guarantees no loss on winning trade)
            if gain_pct >= 0.08:
                be_price = round(pos.entry_price * 1.025, 2)
                if pos.trailing_sl is None or be_price > pos.trailing_sl:
                    pos.trailing_sl = be_price
                    print(f"\n[🛡️ TRAILING STOP RATCHET] Breakeven locked @ ₹{be_price:.2f} for {pos.option_symbol}")

            # Rule 2: Lock +8% Profit at +15% gain
            if gain_pct >= 0.15:
                l1 = round(pos.entry_price * 1.08, 2)
                if pos.trailing_sl is None or l1 > pos.trailing_sl:
                    pos.trailing_sl = l1
                    print(f"\n[⭐ TRAILING STOP RATCHET] +8% Profit locked @ ₹{l1:.2f} for {pos.option_symbol}")

            # Rule 3: Lock +16% Profit at +24% gain
            if gain_pct >= 0.24:
                l2 = round(pos.entry_price * 1.16, 2)
                if pos.trailing_sl is None or l2 > pos.trailing_sl:
                    pos.trailing_sl = l2
                    print(f"\n[🚀 TRAILING STOP RATCHET] +16% Momentum Profit locked @ ₹{l2:.2f} for {pos.option_symbol}")

            Repository.save_or_update_position(pos)

            # Check Exit Conditions:
            should_exit = False
            exit_reason = ""

            # 1. Mandatory Square-off at 15:15 IST
            if MarketSessionManager.is_mandatory_square_off_time(bar.timestamp):
                should_exit = True
                exit_reason = "INTRADAY_MANDATORY_SQUARE_OFF"
            # 2. Target Hit (+30% gain or reached target price)
            elif (pos.target and cur_prem >= pos.target) or gain_pct >= 0.30:
                should_exit = True
                exit_reason = "TARGET_HIT_30PCT"
            # 3. Trailing Stop / Breakeven Hit
            elif pos.trailing_sl and cur_prem <= pos.trailing_sl:
                should_exit = True
                exit_reason = "TRAILING_PROFIT_LOCK_HIT" if pos.trailing_sl >= pos.entry_price * 1.05 else "BREAKEVEN_PROFIT_HIT"
            # 4. Hard Stop Loss Hit
            elif pos.stop_loss and cur_prem <= pos.stop_loss:
                should_exit = True
                exit_reason = "STOP_LOSS_HIT"

            if should_exit:
                self._execute_exit(pos, cur_prem, exit_reason, bar.timestamp, regime.value)

        # 4. If outside 09:30 - 14:30 entry window, skip new setups
        if not MarketSessionManager.can_open_new_position(bar.timestamp):
            self.ema_20_prev = bar.ema_20
            self.prev_bar = bar
            return {"status": "SESSION_RESTRICTED"}

        # Update price history for Donchian and Key Levels
        self.highs_history.append(bar.high)
        self.lows_history.append(bar.low)
        if len(self.highs_history) > 20: self.highs_history.pop(0)
        if len(self.lows_history) > 20: self.lows_history.pop(0)
        donch_high = max(self.highs_history[:-1]) if len(self.highs_history) > 1 else bar.high
        donch_low = min(self.lows_history[:-1]) if len(self.lows_history) > 1 else bar.low

        if self.day_open_price is None:
            self.day_open_price = bar.open

        if is_or_ready and self.first_15m_high is None:
            self.first_15m_high = or_h
            self.first_15m_low = or_l

        pivot_p = (bar.high + bar.low + bar.close) / 3.0
        pivot_r1 = 2 * pivot_p - bar.low
        pivot_s1 = 2 * pivot_p - bar.high

        # 5. Evaluate Core Alpha Strategies
        candidate_signals = []

        # Donchian Breakout
        s_donch = self.strat_donchian.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol, avg_atr_14=avg_atr,
            donchian_high=donch_high, donchian_low=donch_low
        )
        if s_donch: candidate_signals.append(s_donch)

        # Breakout Volume
        s_bvol = self.strat_breakout_vol.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol, avg_atr_14=avg_atr,
            swing_high=swing_h, swing_low=swing_l
        )
        if s_bvol: candidate_signals.append(s_bvol)

        # Pivot Reversal
        s_piv = self.strat_pivot.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol, avg_atr_14=avg_atr,
            pivot_r1=pivot_r1, pivot_s1=pivot_s1
        )
        if s_piv: candidate_signals.append(s_piv)

        # Gap Continuation
        if self.first_15m_high and self.day_open_price:
            s_gap = self.strat_gap.evaluate_candle(
                bar=bar, regime=regime, avg_volume_20=avg_vol, avg_atr_14=avg_atr,
                prev_day_close=self.day_open_price * 0.997,
                day_open=self.day_open_price,
                first_15m_high=self.first_15m_high,
                first_15m_low=self.first_15m_low
            )
            if s_gap: candidate_signals.append(s_gap)

        # ORB
        s_orb = self.strat_orb.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol, avg_atr_14=avg_atr,
            or_high=or_h, or_low=or_l, is_or_established=is_or_ready
        )
        if s_orb: candidate_signals.append(s_orb)

        # VWAP EMA
        s_ve = self.strat_vwap_ema.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol, avg_atr_14=avg_atr,
            ema_20_prev=self.ema_20_prev
        )
        if s_ve: candidate_signals.append(s_ve)

        # 6. Signal Validation & Order Execution
        for sig in candidate_signals:
            Repository.record_signal(sig)
            if not sig.is_accepted:
                continue

            can_trade, risk_reason = self.risk_validator.can_execute_trade(sig, bar.timestamp)
            if not can_trade:
                sig.is_accepted = False
                sig.rejection_reason = risk_reason
                continue

            opt_type = OptionType.CE if sig.direction == SignalDirection.BUY_CE else OptionType.PE
            expiry = OptionStrikeSelector.get_nearest_expiry(self.underlying, bar.timestamp)

            # Adaptive Strike Selection to guarantee budget fit
            strike, prem = OptionStrikeSelector.select_strike_for_risk_budget(
                underlying=self.underlying,
                spot_price=bar.close,
                option_type=opt_type,
                expiry=expiry,
                current_dt=bar.timestamp,
                max_risk_amount=settings.max_risk_amount,
                stop_loss_pct=0.15
            )

            symbol = OptionStrikeSelector.generate_option_symbol(self.underlying, expiry, strike, opt_type)
            lot_size = LOT_SIZES[self.underlying]

            # Contract affordability & spread validation
            is_valid, val_reason = OptionValidator.validate(
                premium=prem,
                lot_size=lot_size,
                available_capital=self.portfolio.cash,
                max_trade_risk_inr=settings.max_risk_amount,
                stop_loss_pct=0.15
            )

            if not is_valid:
                sig.is_accepted = False
                sig.rejection_reason = val_reason
                continue

            # Enter Position
            sl = round(prem * 0.85, 2)
            tgt = round(prem * 1.30, 2)
            sig.suggested_strike = strike
            sig.suggested_expiry = expiry
            sig.metadata["option_type"] = opt_type.value

            order = self.broker.buy(
                symbol=symbol,
                quantity=lot_size,
                requested_price=prem,
                stop_loss=sl,
                target=tgt,
                signal=sig,
                dt=bar.timestamp
            )

            print(f"\n[🚀 PAPER ORDER EXECUTED] {symbol} @ ₹{order.executed_price:.2f} [{sig.strategy_id.value} Score: {sig.signal_score}]")

            # Telegram Alert
            TelegramAlertService.alert_paper_entry(
                underlying=self.underlying.value,
                symbol=symbol,
                direction=sig.direction.value,
                entry_price=order.executed_price or prem,
                stop_loss=sl,
                target=tgt,
                strategy=sig.strategy_id.value,
                score=sig.signal_score,
                risk_amount=round((order.executed_price or prem) * 0.15 * lot_size, 2)
            )
            break

        self.ema_20_prev = bar.ema_20
        self.prev_bar = bar
        return {"status": "SUCCESS"}

    def _execute_exit(self, pos: Position, cur_prem: float, reason: str, dt: datetime, regime: str):
        order = self.broker.sell(
            symbol=pos.option_symbol,
            quantity=pos.quantity,
            requested_price=cur_prem,
            reason=reason,
            dt=dt,
            regime=regime
        )
        print(f"\n[🎯 PAPER ORDER CLOSED] {pos.option_symbol} @ ₹{order.executed_price:.2f} (Reason: {reason})")

        if self.portfolio.daily_loss_limit_hit:
            print(f"\n[🚨 CIRCUIT BREAKER] Max Daily Loss Reached! Halting trading for the day.")
            TelegramAlertService.alert_circuit_breaker(
                reason="Daily Loss Limit (₹450 / 3%) Exceeded",
                daily_loss=abs(self.portfolio.daily_realized_pnl)
            )
