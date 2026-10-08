from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class PullbackContinuationStrategy(BaseStrategy):
    """
    Strategy 3: Pullback Continuation (PULLBACK-v1.0)
    Enters established trends on high-probability retracements to dynamic support/resistance (EMA20/VWAP).
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.PULLBACK, version="v1.0")

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        prev_bar: Optional[Bar] = None,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()

        # Operational window: 10:00 to 14:00
        if not (time(10, 0) <= bar_time <= time(14, 0)):
            return None

        if not (bar.vwap and bar.ema_20 and bar.ema_50 and bar.rsi_14 and prev_bar):
            return None

        vol_ratio = (bar.volume / avg_volume_20) if avg_volume_20 > 0 else 1.0

        # Bullish Pullback to EMA20/VWAP in Uptrend
        if (regime in (MarketRegime.STRONG_BULLISH, MarketRegime.WEAK_BULLISH) and
            bar.ema_20 > bar.ema_50 and
            bar.close > bar.vwap and
            bar.low <= bar.ema_20 * 1.001 and  # Touched or dipped slightly to EMA20
            bar.close >= bar.ema_20 and         # Rejected and closed above EMA20
            bar.close > bar.open and            # Green rejection candle
            bar.rsi_14 >= 50.0 and
            bar.volume > prev_bar.volume):

            # Measure lower shadow rejection
            lower_shadow = min(bar.open, bar.close) - bar.low
            candle_body = abs(bar.close - bar.open)
            trigger_score = 17.0 if lower_shadow >= candle_body * 0.5 else 13.0

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
                metadata={"pullback_ema": bar.ema_20, "lower_shadow": lower_shadow}
            )

        # Bearish Pullback to EMA20/VWAP in Downtrend
        if (regime in (MarketRegime.STRONG_BEARISH, MarketRegime.WEAK_BEARISH) and
            bar.ema_20 < bar.ema_50 and
            bar.close < bar.vwap and
            bar.high >= bar.ema_20 * 0.999 and # Bounced to EMA20
            bar.close <= bar.ema_20 and         # Rejected and closed below EMA20
            bar.close < bar.open and            # Red rejection candle
            bar.rsi_14 <= 50.0 and
            bar.volume > prev_bar.volume):

            upper_shadow = bar.high - max(bar.open, bar.close)
            candle_body = abs(bar.close - bar.open)
            trigger_score = 17.0 if upper_shadow >= candle_body * 0.5 else 13.0

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
                metadata={"pullback_ema": bar.ema_20, "upper_shadow": upper_shadow}
            )

        return None

    def check_exit(
        self,
        position: Position,
        current_option_price: float,
        underlying_bar: Bar
    ) -> Tuple[bool, str]:
        # 1. Stop loss hit on option premium
        if current_option_price <= position.stop_loss:
            return True, "STOP_LOSS_PREMIUM_HIT"

        # 2. Target hit (1:1.8 R:R)
        if current_option_price >= position.target:
            return True, "TARGET_HIT"

        # 3. Mandatory square-off
        if underlying_bar.timestamp.time() >= time(15, 15):
            return True, "INTRADAY_MANDATORY_SQUARE_OFF"

        return False, ""
