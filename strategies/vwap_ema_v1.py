from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class VWAPEMAStrategy(BaseStrategy):
    """
    Strategy 2: VWAP + EMA Trend Following (VWAP-EMA-v1.0)
    Captures established intraday directional trends with momentum confirmation.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.VWAP_EMA, version="v1.0")

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        ema_20_prev: Optional[float] = None,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()

        # Operational window: 09:45 to 14:30
        if not (time(9, 45) <= bar_time <= time(14, 30)):
            return None

        if not (bar.vwap and bar.ema_20 and bar.ema_50 and bar.rsi_14 and bar.atr_14):
            return None

        vol_ratio = (bar.volume / avg_volume_20) if avg_volume_20 > 0 else 1.0

        # Bullish Trend (BUY CE)
        if (regime == MarketRegime.STRONG_BULLISH and
            bar.close > bar.vwap and
            bar.ema_20 > bar.ema_50 and
            58.0 <= bar.rsi_14 <= 74.0 and
            (ema_20_prev is None or bar.ema_20 > ema_20_prev)):

            trigger_score = 16.0
            score, breakdown = SignalScorer.score(
                bar=bar,
                direction=SignalDirection.BUY_CE,
                regime=regime,
                trigger_quality_score=trigger_score,
                volume_ratio=vol_ratio,
                avg_atr=avg_atr_14
            )

            is_accepted = score >= SignalScorer.MINIMUM_TRADE_SCORE
            rejection = None if is_accepted else f"SCORE_BELOW_THRESHOLD_{score}"

            return Signal(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                timestamp=bar.timestamp,
                underlying=bar.symbol,
                direction=SignalDirection.BUY_CE,
                signal_score=score,
                market_regime=regime,
                underlying_price=bar.close,
                is_accepted=is_accepted,
                rejection_reason=rejection,
                score_breakdown=breakdown,
                metadata={"ema_20": bar.ema_20, "ema_50": bar.ema_50, "vwap": bar.vwap}
            )

        # Bearish Trend (BUY PE)
        if (regime == MarketRegime.STRONG_BEARISH and
            bar.close < bar.vwap and
            bar.ema_20 < bar.ema_50 and
            26.0 <= bar.rsi_14 <= 42.0 and
            (ema_20_prev is None or bar.ema_20 < ema_20_prev)):

            trigger_score = 16.0
            score, breakdown = SignalScorer.score(
                bar=bar,
                direction=SignalDirection.BUY_PE,
                regime=regime,
                trigger_quality_score=trigger_score,
                volume_ratio=vol_ratio,
                avg_atr=avg_atr_14
            )

            is_accepted = score >= SignalScorer.MINIMUM_TRADE_SCORE
            rejection = None if is_accepted else f"SCORE_BELOW_THRESHOLD_{score}"

            return Signal(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                timestamp=bar.timestamp,
                underlying=bar.symbol,
                direction=SignalDirection.BUY_PE,
                signal_score=score,
                market_regime=regime,
                underlying_price=bar.close,
                is_accepted=is_accepted,
                rejection_reason=rejection,
                score_breakdown=breakdown,
                metadata={"ema_20": bar.ema_20, "ema_50": bar.ema_50, "vwap": bar.vwap}
            )

        return None

    def check_exit(
        self,
        position: Position,
        current_option_price: float,
        underlying_bar: Bar
    ) -> Tuple[bool, str]:
        # 1. Stop loss hit on option premium
        if current_option_price <= position.stop_loss:
            return True, "STOP_LOSS_PREMIUM_HIT"

        # 2. Target hit (1:2 R:R)
        if current_option_price >= position.target:
            return True, "TARGET_HIT"

        # 3. Macro Trend Invalidation: Underlying closes on opposite side of VWAP with RSI breakdown
        if underlying_bar.vwap and underlying_bar.rsi_14:
            if position.option_type.value == "CE" and underlying_bar.close < underlying_bar.vwap and underlying_bar.rsi_14 < 48:
                return True, "VWAP_TREND_BROKEN"
            elif position.option_type.value == "PE" and underlying_bar.close > underlying_bar.vwap and underlying_bar.rsi_14 > 52:
                return True, "VWAP_TREND_BROKEN"

        # 4. Mandatory square-off at 15:15
        if underlying_bar.timestamp.time() >= time(15, 15):
            return True, "INTRADAY_MANDATORY_SQUARE_OFF"

        return False, ""
