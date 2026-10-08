from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class DonchianBreakoutStrategy(BaseStrategy):
    """
    Strategy 11: Donchian Channel Dynamic Range Breakout (DONCHIAN-v1.0)
    Quant breakout strategy tracking 20-bar channel boundaries.
    Executes on explosive multi-bar high/low violations with institutional volume.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.DONCHIAN, version="v1.0")
        self.strategy_name = "DONCHIAN"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        donchian_high: Optional[float] = None,
        donchian_low: Optional[float] = None,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()
        if not (time(9, 30) <= bar_time <= time(14, 15)):
            return None

        if not (donchian_high and donchian_low and bar.vwap and bar.rsi_14 and avg_volume_20 > 0):
            return None

        vol_ratio = bar.volume / avg_volume_20

        # Bullish Donchian 20-bar High Violation (BUY CE)
        if (bar.close > donchian_high and
            bar.close > bar.vwap and
            bar.rsi_14 >= 55.0 and
            vol_ratio >= 1.20 and
            regime not in (MarketRegime.STRONG_BEARISH, MarketRegime.SIDEWAYS)):

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
                    "donchian_high": donchian_high,
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        # Bearish Donchian 20-bar Low Violation (BUY PE)
        elif (bar.close < donchian_low and
              bar.close < bar.vwap and
              bar.rsi_14 <= 45.0 and
              vol_ratio >= 1.20 and
              regime not in (MarketRegime.STRONG_BULLISH, MarketRegime.SIDEWAYS)):

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
                    "donchian_low": donchian_low,
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
