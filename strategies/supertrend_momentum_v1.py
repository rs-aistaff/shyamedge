from datetime import time
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position
from strategies.base import BaseStrategy
from strategies.signal_scorer import SignalScorer

class SupertrendMomentumStrategy(BaseStrategy):
    """
    Strategy 7: Supertrend Momentum & Volatility Expansion (SUPERTREND-MOM-v1.0)
    High-momentum intraday trend reversal and acceleration system.
    Identifies dynamic volatility band flips confirmed by VWAP and RSI momentum.
    """
    def __init__(self):
        super().__init__(strategy_id=StrategyID.SUPERTREND_MOM, version="v1.0")
        self.strategy_name = "SUPERTREND_MOM"

    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        supertrend_direction: Optional[int] = None, # +1 = Bullish, -1 = Bearish
        supertrend_flipped: bool = False,
        **kwargs
    ) -> Optional[Signal]:
        bar_time = bar.timestamp.time()
        if not (time(9, 30) <= bar_time <= time(14, 15)):
            return None

        if not (bar.vwap and bar.rsi_14 and avg_volume_20 > 0):
            return None

        vol_ratio = bar.volume / avg_volume_20

        # Bullish Supertrend Momentum Setup (BUY CE)
        if (supertrend_direction == 1 and
            bar.close > bar.vwap and
            bar.rsi_14 >= 55.0 and
            vol_ratio >= 1.15 and
            regime in (MarketRegime.STRONG_BULLISH, MarketRegime.WEAK_BULLISH, MarketRegime.HIGH_VOLATILITY)):

            trigger_score = 19.0 if supertrend_flipped else 15.0
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
                    "supertrend_direction": supertrend_direction,
                    "supertrend_flipped": supertrend_flipped,
                    "volume_ratio": round(vol_ratio, 2)
                }
            )

        # Bearish Supertrend Momentum Setup (BUY PE)
        elif (supertrend_direction == -1 and
              bar.close < bar.vwap and
              bar.rsi_14 <= 45.0 and
              vol_ratio >= 1.15 and
              regime in (MarketRegime.STRONG_BEARISH, MarketRegime.WEAK_BEARISH, MarketRegime.HIGH_VOLATILITY)):

            trigger_score = 19.0 if supertrend_flipped else 15.0
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
                    "supertrend_direction": supertrend_direction,
                    "supertrend_flipped": supertrend_flipped,
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

        # 3. Supertrend Trend Invalidation
        if position.option_type.value == "CE" and underlying_bar.vwap:
            if underlying_bar.close < underlying_bar.vwap and underlying_bar.rsi_14 and underlying_bar.rsi_14 < 45:
                return True, "TREND_MOMENTUM_LOST"
        elif position.option_type.value == "PE" and underlying_bar.vwap:
            if underlying_bar.close > underlying_bar.vwap and underlying_bar.rsi_14 and underlying_bar.rsi_14 > 55:
                return True, "TREND_MOMENTUM_LOST"

        # 4. Trailing Stop Loss
        if position.trailing_sl and current_option_price <= position.trailing_sl:
            return True, "TRAILING_SL_HIT"

        # 5. End of Day Square-Off at 15:15 IST
        if underlying_bar.timestamp.time() >= time(15, 15):
            return True, "EOD_SQUARE_OFF"

        return False, "HOLD"
