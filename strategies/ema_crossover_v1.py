from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class EMACrossoverStrategy(BaseStrategy):
    """
    Strategy 10: 9/21 EMA Fast Ribbon Crossover (EMA-CROSS-v1.0)
    Classic fast momentum ribbon system filtered by the macro 50 EMA and VWAP.
    Detects early acceleration swings in trending options contracts.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.EMA_CROSSOVER, version="v1.0")
        self.strategy_name = "EMA_CROSSOVER"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        ema_9: Optional[float] = None,
        ema_9_prev: Optional[float] = None,
        ema_21: Optional[float] = None,
        ema_21_prev: Optional[float] = None,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()
        if not (time(9, 30) <= bar_time <= time(14, 0)):
            return None

        if not (ema_9 and ema_9_prev and ema_21 and ema_21_prev and bar.ema_50 and bar.vwap and avg_volume_20 > 0):
            return None

        vol_ratio = bar.volume / avg_volume_20

        # Bullish 9/21 EMA Golden Cross
        if (ema_9_prev <= ema_21_prev and ema_9 > ema_21 and
            bar.close > bar.ema_50 and
            bar.close > bar.vwap and
            vol_ratio >= 1.15 and
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
                    "ema_9": round(ema_9, 2),
                    "ema_21": round(ema_21, 2),
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        # Bearish 9/21 EMA Death Cross
        elif (ema_9_prev >= ema_21_prev and ema_9 < ema_21 and
              bar.close < bar.ema_50 and
              bar.close < bar.vwap and
              vol_ratio >= 1.15 and
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
                    "ema_9": round(ema_9, 2),
                    "ema_21": round(ema_21, 2),
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
