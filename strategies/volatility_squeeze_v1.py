from datetime import time
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class VolatilitySqueezeStrategy(BaseStrategy):
    """
    Strategy 6: Volatility Squeeze Momentum (SQUEEZE-v1.0)
    Detects low-volatility compression (Bollinger Bands inside Keltner Channel)
    and enters as momentum fires directionally with explosive options premium expansion.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.VOL_SQUEEZE, version="v1.0")
        self.strategy_name = "VOLATILITY_SQUEEZE"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        bb_upper: Optional[float] = None,
        bb_lower: Optional[float] = None,
        kc_upper: Optional[float] = None,
        kc_lower: Optional[float] = None,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()

        if not (time(9, 45) <= bar_time <= time(14, 15)):
            return None

        if not (bb_upper and bb_lower and kc_upper and kc_lower and bar.vwap and bar.rsi_14):
            return None

        vol_ratio = (bar.volume / avg_volume_20) if avg_volume_20 > 0 else 1.0

        # Squeeze firing condition: BB band expanding outside Keltner channel
        is_firing_long = bb_upper > kc_upper and bar.close > bar.vwap and bar.rsi_14 >= 58.0
        is_firing_short = bb_lower < kc_lower and bar.close < bar.vwap and bar.rsi_14 <= 42.0

        if is_firing_long and regime != MarketRegime.SIDEWAYS:
            score, breakdown = SignalScorer.score(
                bar=bar,
                direction=SignalDirection.BUY_CE,
                regime=regime,
                trigger_quality_score=19.0,
                volume_ratio=vol_ratio,
                avg_atr=avg_atr_14
            )
            is_accepted = score >= 70.0
            return Signal(
                strategy_id=StrategyID.VWAP_EMA,
                strategy_version="SQUEEZE-v1.0",
                timestamp=bar.timestamp,
                underlying=bar.symbol,
                direction=SignalDirection.BUY_CE,
                signal_score=score,
                market_regime=regime,
                underlying_price=bar.close,
                is_accepted=is_accepted,
                rejection_reason=None if is_accepted else f"SCORE_BELOW_THRESHOLD_{score}",
                score_breakdown=breakdown
            )

        if is_firing_short and regime != MarketRegime.SIDEWAYS:
            score, breakdown = SignalScorer.score(
                bar=bar,
                direction=SignalDirection.BUY_PE,
                regime=regime,
                trigger_quality_score=19.0,
                volume_ratio=vol_ratio,
                avg_atr=avg_atr_14
            )
            is_accepted = score >= 70.0
            return Signal(
                strategy_id=StrategyID.VWAP_EMA,
                strategy_version="SQUEEZE-v1.0",
                timestamp=bar.timestamp,
                underlying=bar.symbol,
                direction=SignalDirection.BUY_PE,
                signal_score=score,
                market_regime=regime,
                underlying_price=bar.close,
                is_accepted=is_accepted,
                rejection_reason=None if is_accepted else f"SCORE_BELOW_THRESHOLD_{score}",
                score_breakdown=breakdown
            )

        return None

    def check_exit(
        self,
        position: Position,
        current_option_price: float,
        underlying_bar: Bar
    ) -> Tuple[bool, str]:
        if current_option_price <= position.stop_loss:
            return True, "STOP_LOSS_PREMIUM_HIT"
        if current_option_price >= position.target:
            return True, "TARGET_HIT"
        if underlying_bar.timestamp.time() >= time(15, 15):
            return True, "INTRADAY_MANDATORY_SQUARE_OFF"
        return False, ""
