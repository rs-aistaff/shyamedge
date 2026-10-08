from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class InsideBarBreakoutStrategy(BaseStrategy):
    """
    Strategy 8: Inside Bar Compression & Breakout (INSIDE-BAR-v1.0)
    Captures volatility compression release when price breaks out of a
    prior mother bar consolidation range with directional volume expansion.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.INSIDE_BAR, version="v1.0")
        self.strategy_name = "INSIDE_BAR"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        prev_bar: Optional[Bar] = None,
        mother_bar: Optional[Bar] = None,
        is_inside_bar_breakout: bool = False,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()
        if not (time(9, 30) <= bar_time <= time(14, 30)):
            return None

        if not (mother_bar and bar.vwap and bar.rsi_14 and avg_volume_20 > 0):
            return None

        vol_ratio = bar.volume / avg_volume_20

        # Bullish Breakout above Mother Bar High (BUY CE)
        if (bar.close > mother_bar.high and
            bar.close > bar.vwap and
            bar.rsi_14 >= 54.0 and
            vol_ratio >= 1.2 and
            regime not in (MarketRegime.STRONG_BEARISH, MarketRegime.SIDEWAYS)):

            trigger_score = 18.0
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
                    "mother_bar_high": mother_bar.high,
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        # Bearish Breakout below Mother Bar Low (BUY PE)
        elif (bar.close < mother_bar.low and
              bar.close < bar.vwap and
              bar.rsi_14 <= 46.0 and
              vol_ratio >= 1.2 and
              regime not in (MarketRegime.STRONG_BULLISH, MarketRegime.SIDEWAYS)):

            trigger_score = 18.0
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
                    "mother_bar_low": mother_bar.low,
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
        # 1. Option Stop Loss Hit (15% SL)
        if current_option_price <= position.stop_loss:
            return True, "OPTION_SL_HIT"

        # 2. Option Target Hit (30% Target, 1:2 R:R)
        if current_option_price >= position.target:
            return True, "OPTION_TARGET_HIT"

        # 3. Trailing SL Hit
        if position.trailing_sl and current_option_price <= position.trailing_sl:
            return True, "TRAILING_SL_HIT"

        # 4. End of Day Square-Off at 15:15 IST
        if underlying_bar.timestamp.time() >= time(15, 15):
            return True, "EOD_SQUARE_OFF"

        return False, "HOLD"
