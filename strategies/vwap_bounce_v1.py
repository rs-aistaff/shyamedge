from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class VWAPBounceStrategy(BaseStrategy):
    """
    Strategy 12: Intraday VWAP Mean-Reversion Rejection Rebound (VWAP-BOUNCE-v1.0)
    Identifies institutional defended VWAP tests during trending days.
    Fires when price wicks into VWAP and aggressively snaps back in trend direction.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.VWAP_BOUNCE, version="v1.0")
        self.strategy_name = "VWAP_BOUNCE"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()
        if not (time(9, 45) <= bar_time <= time(14, 15)):
            return None

        if not (bar.vwap and bar.rsi_14 and avg_volume_20 > 0):
            return None

        vol_ratio = bar.volume / avg_volume_20

        # Bullish VWAP Rejection Bounce (Tests VWAP from above and bounces green)
        is_bullish_bounce = (
            bar.low <= bar.vwap and
            bar.close > bar.vwap and
            bar.close > bar.open and
            (bar.close - bar.open) >= (bar.high - bar.low) * 0.40 and  # solid green body
            bar.rsi_14 >= 52.0 and
            vol_ratio >= 1.10 and
            regime in (MarketRegime.STRONG_BULLISH, MarketRegime.WEAK_BULLISH)
        )

        if is_bullish_bounce:
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
                    "vwap": round(bar.vwap, 2),
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        # Bearish VWAP Rejection Bounce (Tests VWAP from below and rejects red)
        is_bearish_bounce = (
            bar.high >= bar.vwap and
            bar.close < bar.vwap and
            bar.close < bar.open and
            (bar.open - bar.close) >= (bar.high - bar.low) * 0.40 and  # solid red body
            bar.rsi_14 <= 48.0 and
            vol_ratio >= 1.10 and
            regime in (MarketRegime.STRONG_BEARISH, MarketRegime.WEAK_BEARISH)
        )

        if is_bearish_bounce:
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
                    "vwap": round(bar.vwap, 2),
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
