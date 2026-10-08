from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class ORBStrategy(BaseStrategy):
    """
    Strategy 1: Opening Range Breakout (ORB-v1.0)
    Captures directional momentum following opening price discovery (09:15-09:30).
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.ORB, version="v1.0")

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        or_high: Optional[float] = None,
        or_low: Optional[float] = None,
        is_or_established: bool = False,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()

        # Signal window: Strictly between 09:30 and 10:30 IST
        if not (time(9, 30) <= bar_time <= time(10, 30)):
            return None

        if not is_or_established or or_high is None or or_low is None:
            return None

        # Filter out sideways / chop regimes
        if regime in (MarketRegime.SIDEWAYS, MarketRegime.UNCLEAR):
            return None

        # ATR range check: Range must not be abnormally wide or thin
        or_range = or_high - or_low
        if bar.atr_14:
            if or_range < (0.4 * bar.atr_14) or or_range > (1.6 * bar.atr_14):
                return None

        vol_ratio = (bar.volume / avg_volume_20) if avg_volume_20 > 0 else 1.0

        # Bullish Breakout (BUY CE)
        if (bar.close > or_high and bar.vwap and bar.close > bar.vwap and
            bar.rsi_14 and bar.rsi_14 >= 55.0 and vol_ratio >= 1.3):

            trigger_score = 18.0 if bar.close > or_high * 1.0005 else 14.0
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
                metadata={"or_high": or_high, "or_low": or_low, "or_range": or_range}
            )

        # Bearish Breakdown (BUY PE)
        if (bar.close < or_low and bar.vwap and bar.close < bar.vwap and
            bar.rsi_14 and bar.rsi_14 <= 45.0 and vol_ratio >= 1.3):

            trigger_score = 18.0 if bar.close < or_low * 0.9995 else 14.0
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
                metadata={"or_high": or_high, "or_low": or_low, "or_range": or_range}
            )

        return None

    def check_exit(
        self,
        position: Position,
        current_option_price: float,
        underlying_bar: Bar
    ) -> Tuple[bool, str]:
        # 1. Stop Loss: 15% loss on option premium
        if current_option_price <= position.stop_loss:
            return True, "STOP_LOSS_PREMIUM_HIT"

        # 2. Target: 1:2 R:R (e.g. +30% gain on 15% risk)
        if current_option_price >= position.target:
            return True, "TARGET_HIT"

        # 3. Time Exit at 14:45 IST
        if underlying_bar.timestamp.time() >= time(14, 45):
            return True, "INTRADAY_TIME_CUTOFF"

        return False, ""
