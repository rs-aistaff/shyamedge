from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class PivotReversalStrategy(BaseStrategy):
    """
    Strategy 15: Daily Floor Pivot R1/S1 Breakout & Trend Continuation (PIVOT-REV-v1.0)
    Executes when price breaks out of the classical Daily Floor Pivot boundaries (R1 / S1)
    with heavy directional participation, signaling strong daily expansion.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.PIVOT_REVERSAL, version="v1.0")
        self.strategy_name = "PIVOT_REVERSAL"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        pivot_r1: Optional[float] = None,
        pivot_s1: Optional[float] = None,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()
        if not (time(9, 30) <= bar_time <= time(14, 0)):
            return None

        if not (pivot_r1 and pivot_s1 and bar.vwap and bar.rsi_14 and avg_volume_20 > 0):
            return None

        vol_ratio = bar.volume / avg_volume_20

        # Bullish R1 Breakout: Price crosses above R1 with momentum above VWAP
        if (bar.close > pivot_r1 and
            bar.close > bar.vwap and
            bar.rsi_14 >= 56.0 and
            vol_ratio >= 1.20 and
            regime != MarketRegime.SIDEWAYS):

            trigger_score = 19.0
            score, breakdown = SignalScorer.score(
                bar=bar,
                direction=SignalDirection.BUY_CE,
                regime=regime,
                trigger_quality_score=trigger_score,
                volume_ratio=vol_ratio,
                avg_atr=avg_atr_14
            )

            is_accepted = score >= 70.0
            rejection = None if is_accepted else f"SCORE_BELOW_THRESHOLD_{score}"

            return Signal(
                timestamp=bar.timestamp,
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                underlying=bar.symbol,
                direction=SignalDirection.BUY_CE,
                signal_score=score,
                market_regime=regime,
                underlying_price=bar.close,
                is_accepted=is_accepted,
                rejection_reason=rejection,
                score_breakdown=breakdown,
                metadata={
                    "pivot_r1": pivot_r1,
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        # Bearish S1 Breakdown: Price crosses below S1 with momentum below VWAP
        elif (bar.close < pivot_s1 and
              bar.close < bar.vwap and
              bar.rsi_14 <= 44.0 and
              vol_ratio >= 1.20 and
              regime != MarketRegime.SIDEWAYS):

            trigger_score = 19.0
            score, breakdown = SignalScorer.score(
                bar=bar,
                direction=SignalDirection.BUY_PE,
                regime=regime,
                trigger_quality_score=trigger_score,
                volume_ratio=vol_ratio,
                avg_atr=avg_atr_14
            )

            is_accepted = score >= 70.0
            rejection = None if is_accepted else f"SCORE_BELOW_THRESHOLD_{score}"

            return Signal(
                timestamp=bar.timestamp,
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                underlying=bar.symbol,
                direction=SignalDirection.BUY_PE,
                signal_score=score,
                market_regime=regime,
                underlying_price=bar.close,
                is_accepted=is_accepted,
                rejection_reason=rejection,
                score_breakdown=breakdown,
                metadata={
                    "pivot_s1": pivot_s1,
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        return None

    def check_exit(
        self,
        position: Position,
        current_option_price: float,
        underlying_bar: Bar
    ) -> Tuple[bool, str]:
        if current_option_price <= position.stop_loss:
            return True, "OPTION_SL_HIT"

        if current_option_price >= position.target:
            return True, "OPTION_TARGET_HIT"

        if position.trailing_sl and current_option_price <= position.trailing_sl:
            return True, "TRAILING_SL_HIT"

        if underlying_bar.timestamp.time() >= time(15, 15):
            return True, "EOD_SQUARE_OFF"

        return False, "HOLD"
