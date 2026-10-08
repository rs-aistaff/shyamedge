import time
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any
from config.settings import settings
from config.trading_hours import MarketSessionManager
from core.constants import Underlying, OptionType, SignalDirection, StrategyID, LOT_SIZES
from core.models import Bar, Signal, Position, Trade
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

logger = logging.getLogger("ShyamEdge.PaperEngine")

class PaperTradingRunner:
    """
    Live Paper Trading Orchestrator for NIFTY 50 and SENSEX.
    Runs all 4 independent strategies simultaneously within the ₹15,000 risk envelope.
    """
    def __init__(self, underlying: Underlying = Underlying.NIFTY50):
        self.underlying = underlying
        self.is_running = False

        # Initialize core portfolio & broker
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

        # Quantitative Trackers
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

    def start(self):
        """Starts the paper trading runner."""
        init_db()
        self.is_running = True
        logger.info(f"ShyamEdge Paper Engine initialized for {self.underlying.value}. Capital: ₹{self.portfolio.current_capital}")
        Repository.log_system_event("PaperEngine", "INFO", f"Engine started for {self.underlying.value}")

    def stop(self):
        """Stops the paper trading runner."""
        self.is_running = False
        logger.info("ShyamEdge Paper Engine stopped.")
        Repository.log_system_event("PaperEngine", "INFO", "Engine stopped")

    def process_candle(self, bar: Bar) -> Dict[str, Any]:
        """
        Processes a newly formed 5-minute candle in real time.
        """
        if not self.is_running:
            return {"status": "STOPPED"}

        # 1. Update Indicators
        bar.vwap = self.vwap_calc.update(bar.timestamp, bar.high, bar.low, bar.close, float(bar.volume))
        bar.ema_20 = self.ema_20_calc.update(bar.close)
        bar.ema_50 = self.ema_50_calc.update(bar.close)
        bar.rsi_14 = self.rsi_calc.update(bar.close)
        bar.atr_14 = self.atr_calc.update(bar.high, bar.low, bar.close)

        or_high, or_low, is_or_ready = self.or_tracker.update(bar)
        swing_h, swing_l = self.levels_tracker.update(bar.high, bar.low)

        self.volume_history.append(bar.volume)
        if len(self.volume_history) > 20: self.volume_history.pop(0)
        avg_vol_20 = sum(self.volume_history) / len(self.volume_history)

        self.atr_history.append(bar.atr_14)
        if len(self.atr_history) > 20: self.atr_history.pop(0)
        avg_atr_20 = sum(self.atr_history) / len(self.atr_history)

        # 2. Market Regime
        regime = self.regime_detector.detect(bar, ema_20_prev=self.ema_20_prev)
        bar.regime = regime

        # 3. Position Management & Exit Surveillance
        pos = self.portfolio.active_position
        if pos:
            current_opt_price = OptionPricingEngine.estimate_premium(
                spot=bar.close,
                strike=pos.strike,
                option_type=pos.option_type,
                expiry=pos.expiry,
                current_dt=bar.timestamp
            )

            # Universal Trailing Stop & Profit Lock Management
            gain_pct = (current_opt_price - pos.entry_price) / pos.entry_price

            # Rule 1: Fast Breakeven Lock at +8% gain
            if gain_pct >= 0.08:
                be_price = round(pos.entry_price * 1.025, 2)
                if pos.trailing_sl is None or be_price > pos.trailing_sl:
                    pos.trailing_sl = be_price

            # Rule 2: Lock +8% Profit at +15% gain
            if gain_pct >= 0.15:
                l1 = round(pos.entry_price * 1.08, 2)
                if pos.trailing_sl is None or l1 > pos.trailing_sl:
                    pos.trailing_sl = l1

            # Rule 3: Lock +16% Profit at +24% gain
            if gain_pct >= 0.24:
                l2 = round(pos.entry_price * 1.16, 2)
                if pos.trailing_sl is None or l2 > pos.trailing_sl:
                    pos.trailing_sl = l2

            # Check Exit Conditions:
            should_exit = False
            exit_reason = ""

            # 1. Mandatory Square-off at 15:15 IST
            if MarketSessionManager.is_mandatory_square_off_time(bar.timestamp):
                should_exit = True
                exit_reason = "INTRADAY_MANDATORY_SQUARE_OFF"
            # 2. Target Hit (+30% gain or reached target price)
            elif (pos.target and current_opt_price >= pos.target) or gain_pct >= 0.30:
                should_exit = True
                exit_reason = "TARGET_HIT_30PCT"
            # 3. Trailing Stop / Breakeven Hit
            elif pos.trailing_sl and current_opt_price <= pos.trailing_sl:
                should_exit = True
                exit_reason = "TRAILING_PROFIT_LOCK_HIT" if pos.trailing_sl >= pos.entry_price * 1.05 else "BREAKEVEN_PROFIT_HIT"
            # 4. Hard Stop Loss Hit
            elif pos.stop_loss and current_opt_price <= pos.stop_loss:
                should_exit = True
                exit_reason = "STOP_LOSS_HIT"

            if should_exit:
                self._execute_exit(pos, current_opt_price, exit_reason, bar.timestamp, regime.value)

        # 4. Check whether we are in active entry window (09:30 - 14:30)
        if not MarketSessionManager.can_open_new_position(bar.timestamp):
            self.ema_20_prev = bar.ema_20
            self.prev_bar = bar
            return {
                "status": "OUTSIDE_ENTRY_WINDOW",
                "regime": regime.value,
                "capital": self.portfolio.current_capital,
                "active_position": self.portfolio.active_position.option_symbol if self.portfolio.active_position else None
            }

        # Update price history for Donchian and Key Levels
        self.highs_history.append(bar.high)
        self.lows_history.append(bar.low)
        if len(self.highs_history) > 20: self.highs_history.pop(0)
        if len(self.lows_history) > 20: self.lows_history.pop(0)
        donch_high = max(self.highs_history[:-1]) if len(self.highs_history) > 1 else bar.high
        donch_low = min(self.lows_history[:-1]) if len(self.lows_history) > 1 else bar.low

        if self.day_open_price is None:
            self.day_open_price = bar.open

        if is_or_established and self.first_15m_high is None:
            self.first_15m_high = or_high
            self.first_15m_low = or_low

        pivot_p = (bar.high + bar.low + bar.close) / 3.0
        pivot_r1 = 2 * pivot_p - bar.low
        pivot_s1 = 2 * pivot_p - bar.high

        # 5. Evaluate Core Alpha Strategies
        candidate_signals = []

        # Donchian Breakout
        s_donch = self.strat_donchian.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol_20, avg_atr_14=avg_atr_20,
            donchian_high=donch_high, donchian_low=donch_low
        )
        if s_donch: candidate_signals.append(s_donch)

        # Breakout Volume
        s_bvol = self.strat_breakout_vol.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol_20, avg_atr_14=avg_atr_20,
            swing_high=swing_h, swing_low=swing_l
        )
        if s_bvol: candidate_signals.append(s_bvol)

        # Pivot Reversal
        s_piv = self.strat_pivot.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol_20, avg_atr_14=avg_atr_20,
            pivot_r1=pivot_r1, pivot_s1=pivot_s1
        )
        if s_piv: candidate_signals.append(s_piv)

        # Gap Continuation
        if self.first_15m_high and self.day_open_price:
            s_gap = self.strat_gap.evaluate_candle(
                bar=bar, regime=regime, avg_volume_20=avg_vol_20, avg_atr_14=avg_atr_20,
                prev_day_close=self.day_open_price * 0.997,
                day_open=self.day_open_price,
                first_15m_high=self.first_15m_high,
                first_15m_low=self.first_15m_low
            )
            if s_gap: candidate_signals.append(s_gap)

        # ORB
        s_orb = self.strat_orb.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol_20, avg_atr_14=avg_atr_20,
            or_high=or_high, or_low=or_low, is_or_established=is_or_established
        )
        if s_orb: candidate_signals.append(s_orb)

        # VWAP EMA
        s_ve = self.strat_vwap_ema.evaluate_candle(
            bar=bar, regime=regime, avg_volume_20=avg_vol_20, avg_atr_14=avg_atr_20,
            ema_20_prev=self.ema_20_prev
        )
        if s_ve: candidate_signals.append(s_ve)

        # 6. Signal Scoring, Risk & Option Allocation
        for sig in candidate_signals:
            Repository.record_signal(sig)

            if not sig.is_accepted:
                continue

            # Risk check
            can_trade, risk_reason = self.risk_validator.can_execute_trade(sig, bar.timestamp)
            if not can_trade:
                sig.is_accepted = False
                sig.rejection_reason = risk_reason
                continue

            # Option Selection
            opt_type = OptionType.CE if sig.direction == SignalDirection.BUY_CE else OptionType.PE
            expiry = OptionStrikeSelector.get_nearest_expiry(self.underlying, bar.timestamp)
            strike = OptionStrikeSelector.select_strike(self.underlying, bar.close, opt_type, prefer_itm=False)
            symbol = OptionStrikeSelector.generate_option_symbol(self.underlying, expiry, strike, opt_type)

            est_premium = OptionPricingEngine.estimate_premium(
                spot=bar.close, strike=strike, option_type=opt_type, expiry=expiry, current_dt=bar.timestamp
            )
            lot_size = LOT_SIZES[self.underlying]

            # Contract validation
            is_valid, val_reason = OptionValidator.validate(
                premium=est_premium,
                lot_size=lot_size,
                available_capital=self.portfolio.cash,
                max_trade_risk_inr=settings.max_risk_amount,
                stop_loss_pct=0.15
            )

            if not is_valid:
                sig.is_accepted = False
                sig.rejection_reason = val_reason
                continue

            # Enter Paper Position
            sl = round(est_premium * 0.85, 2)
            tgt = round(est_premium * 1.30, 2)
            sig.suggested_strike = strike
            sig.suggested_expiry = expiry
            sig.metadata["option_type"] = opt_type.value

            order = self.broker.buy(
                symbol=symbol,
                quantity=lot_size,
                requested_price=est_premium,
                stop_loss=sl,
                target=tgt,
                signal=sig,
                dt=bar.timestamp
            )

            # Alert via Telegram
            TelegramAlertService.alert_paper_entry(
                underlying=self.underlying.value,
                symbol=symbol,
                direction=sig.direction.value,
                entry_price=order.executed_price or est_premium,
                stop_loss=sl,
                target=tgt,
                strategy=sig.strategy_id.value,
                score=sig.signal_score,
                risk_amount=round((order.executed_price or est_premium) * 0.15 * lot_size, 2)
            )

            logger.info(f"PAPER ORDER EXECUTED: {symbol} @ ₹{order.executed_price} [{sig.strategy_id.value}]")
            break  # Only one position allowed at a time

        self.ema_20_prev = bar.ema_20
        self.prev_bar = bar

        return {
            "status": "OK",
            "time": bar.timestamp.isoformat(),
            "close": bar.close,
            "regime": regime.value,
            "capital": self.portfolio.current_capital,
            "active_position": self.portfolio.active_position.option_symbol if self.portfolio.active_position else None
        }

    def _execute_exit(self, pos: Position, current_price: float, reason: str, dt: datetime, regime: str):
        order = self.broker.sell(
            symbol=pos.option_symbol,
            quantity=pos.quantity,
            requested_price=current_price,
            reason=reason,
            dt=dt,
            regime=regime
        )
        logger.info(f"PAPER ORDER CLOSED: {pos.option_symbol} @ ₹{order.executed_price} (Reason: {reason})")

        # Check circuit breaker
        if self.portfolio.daily_loss_limit_hit:
            TelegramAlertService.alert_circuit_breaker(
                reason="Daily Loss Limit (₹450 / 3%) Exceeded",
                daily_loss=abs(self.portfolio.daily_realized_pnl)
            )
