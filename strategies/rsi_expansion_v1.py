from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class RSIExpansionStrategy(BaseStrategy):
    """
    Strategy 9: RSI Momentum Range Shift & Expansion (RSI-EXPANSION-v1.0)
    Based on Andrew Cardwell's range shift theory.
    Fires when RSI surges across 60 (super-bullish momentum) or sinks below 40 (super-bearish momentum)
    with VWAP directional alignment.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.RSI_EXPANSION, version="v1.0")
        self.strategy_name = "RSI_EXPANSION"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        rsi_prev: Optional[float] = None,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()
        if not (time(9, 30) <= bar_time <= time(14, 15)):
            return None

        if not (bar.vwap and bar.rsi_14 and rsi_prev and avg_volume_20 > 0):
            return None

        vol_ratio = bar.volume / avg_volume_20

        # Bullish RSI Range Shift (Crosses above 60 with price above VWAP)
        if (rsi_prev < 60.0 and bar.rsi_14 >= 60.0 and
            bar.close > bar.vwap and
            vol_ratio >= 1.10 and
            regime in (MarketRegime.STRONG_BULLISH, MarketRegime.WEAK_BULLISH, MarketRegime.HIGH_VOLATILITY)):

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
                    "rsi": round(bar.rsi_14, 2),
                    "rsi_prev": round(rsi_prev, 2),
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        # Bearish RSI Range Shift (Crosses below 40 with price below VWAP)
        elif (rsi_prev > 40.0 and bar.rsi_14 <= 40.0 and
              bar.close < bar.vwap and
              vol_ratio >= 1.10 and
              regime in (MarketRegime.STRONG_BEARISH, MarketRegime.WEAK_BEARISH, MarketRegime.HIGH_VOLATILITY)):

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
                    "rsi": round(bar.rsi_14, 2),
                    "rsi_prev": round(rsi_prev, 2),
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

        # RSI Momentum Exhaustion Exit
        if position.option_type.value == "CE" and underlying_bar.rsi_14 and underlying_bar.rsi_14 < 50:
            return True, "RSI_BULL_MOMENTUM_LOST"
        elif position.option_type.value == "PE" and underlying_bar.rsi_14 and underlying_bar.rsi_14 > 50:
            return True, "RSI_BEAR_MOMENTUM_LOST"

        if position.trailing_sl and current_option_price <= position.trailing_sl:
            return True, "TRAILING_SL_HIT"

        if underlying_bar.timestamp.time() >= time(15, 15):
            return True, "EOD_SQUARE_OFF"

        return False, "HOLD"
