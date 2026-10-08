from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class BreakoutVolumeStrategy(BaseStrategy):
    """
    Strategy 4: Breakout + Volume (BREAKOUT-VOL-v1.0)
    Monitors high-conviction level breakouts confirmed by institutional volume surges (>= 1.8x SMA20).
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.BREAKOUT_VOL, version="v1.0")

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        swing_high: Optional[float] = None,
        swing_low: Optional[float] = None,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()

        # Operational window: 09:45 to 14:15
        if not (time(9, 45) <= bar_time <= time(14, 15)):
            return None

        if not (swing_high and swing_low and bar.vwap and bar.rsi_14 and avg_volume_20 > 0):
            return None

        vol_ratio = bar.volume / avg_volume_20

        # Require significant volume spike
        if vol_ratio < 1.7:
            return None

        candle_range = max(bar.high - bar.low, 0.05)

        # Bullish Level Breakout (BUY CE)
        if (bar.close > swing_high and
            bar.close > bar.vwap and
            bar.rsi_14 >= 58.0 and
            regime != MarketRegime.SIDEWAYS):

            # False breakout filter: Upper wick must not be excessive (> 35% of range)
            upper_wick = bar.high - max(bar.open, bar.close)
            if upper_wick / candle_range > 0.35:
                return None  # Rejection at top

            trigger_score = 19.0
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
                metadata={"broken_level": swing_high, "vol_ratio": vol_ratio}
            )

        # Bearish Level Breakdown (BUY PE)
        if (bar.close < swing_low and
            bar.close < bar.vwap and
            bar.rsi_14 <= 42.0 and
            regime != MarketRegime.SIDEWAYS):

            # False breakdown filter: Lower wick must not be excessive (> 35% of range)
            lower_wick = min(bar.open, bar.close) - bar.low
            if lower_wick / candle_range > 0.35:
                return None  # Rejection at bottom

            trigger_score = 19.0
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
                metadata={"broken_level": swing_low, "vol_ratio": vol_ratio}
            )

        return None

    def check_exit(
        self,
        position: Position,
        current_option_price: float,
        underlying_bar: Bar
    ) -> Tuple[bool, str]:
        # 1. Stop loss hit on option premium (18% max stop)
        if current_option_price <= position.stop_loss:
            return True, "STOP_LOSS_PREMIUM_HIT"

        # 2. Target hit (1:2 R:R)
        if current_option_price >= position.target:
            return True, "TARGET_HIT"

        # 3. Mandatory square-off
        if underlying_bar.timestamp.time() >= time(15, 15):
            return True, "INTRADAY_MANDATORY_SQUARE_OFF"

        return False, ""
