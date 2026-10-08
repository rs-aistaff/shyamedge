from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class GapContinuationStrategy(BaseStrategy):
    """
    Strategy 13: Morning Gap & Go Momentum Continuation (GAP-GO-v1.0)
    Executes in opening session (09:30 to 11:00) when overnight gap holds
    and institutional trend continuation drives new highs/lows.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.GAP_CONTINUATION, version="v1.0")
        self.strategy_name = "GAP_CONTINUATION"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        prev_day_close: Optional[float] = None,
        day_open: Optional[float] = None,
        first_15m_high: Optional[float] = None,
        first_15m_low: Optional[float] = None,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()
        # Morning momentum window only: 09:30 to 11:00
        if not (time(9, 30) <= bar_time <= time(11, 0)):
            return None

        if not (prev_day_close and day_open and first_15m_high and first_15m_low and bar.vwap and avg_volume_20 > 0):
            return None

        gap_pct = (day_open - prev_day_close) / prev_day_close
        vol_ratio = bar.volume / avg_volume_20

        # Bullish Gap & Go: Gap Up >= +0.25%, price above VWAP & Day Open, breaks first 15m high
        if (gap_pct >= 0.0025 and
            bar.close > first_15m_high and
            bar.close > bar.vwap and
            bar.close > day_open and
            vol_ratio >= 1.15 and
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
                    "gap_pct": round(gap_pct * 100, 2),
                    "first_15m_high": first_15m_high,
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        # Bearish Gap & Go: Gap Down <= -0.25%, price below VWAP & Day Open, breaks first 15m low
        elif (gap_pct <= -0.0025 and
              bar.close < first_15m_low and
              bar.close < bar.vwap and
              bar.close < day_open and
              vol_ratio >= 1.15 and
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
                    "gap_pct": round(gap_pct * 100, 2),
                    "first_15m_low": first_15m_low,
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
