from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class ATRSurgeStrategy(BaseStrategy):
    """
    Strategy 14: Multi-ATR Directional Candle Expansion (ATR-SURGE-v1.0)
    Fires on institutional ignition candles where candle real body expands
    beyond 1.6x the 14-period ATR with dominant close near bar extremes.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.ATR_SURGE, version="v1.0")
        self.strategy_name = "ATR_SURGE"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()
        if not (time(9, 30) <= bar_time <= time(14, 15)):
            return None

        if not (bar.vwap and bar.rsi_14 and avg_volume_20 > 0 and avg_atr_14 > 0):
            return None

        candle_body = abs(bar.close - bar.open)
        candle_range = max(0.01, bar.high - bar.low)
        vol_ratio = bar.volume / avg_volume_20

        # Bullish ATR Explosion: Body >= 1.5x ATR, close near high, green body, above VWAP
        if (candle_body >= 1.5 * avg_atr_14 and
            bar.close > bar.open and
            (bar.high - bar.close) <= 0.20 * candle_range and # close near high
            bar.close > bar.vwap and
            vol_ratio >= 1.30 and
            regime != MarketRegime.SIDEWAYS):

            trigger_score = 20.0
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
                    "body_atr_ratio": round(candle_body / avg_atr_14, 2),
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        # Bearish ATR Explosion: Body >= 1.5x ATR, close near low, red body, below VWAP
        elif (candle_body >= 1.5 * avg_atr_14 and
              bar.close < bar.open and
              (bar.close - bar.low) <= 0.20 * candle_range and # close near low
              bar.close < bar.vwap and
              vol_ratio >= 1.30 and
              regime != MarketRegime.SIDEWAYS):

            trigger_score = 20.0
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
                    "body_atr_ratio": round(candle_body / avg_atr_14, 2),
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
