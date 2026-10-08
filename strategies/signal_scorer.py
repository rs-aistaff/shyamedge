from typing import Dict, Tuple
from core.constants import MarketRegime, SignalDirection
from core.models import Bar

class SignalScorer:
    """
    Evaluates trading candidate setups and returns a composite 0-100 score
    with itemized factor attribution.
    """
    MINIMUM_TRADE_SCORE = 75.0
    WATCHLIST_SCORE = 60.0

    @classmethod
    def score(
        cls,
        bar: Bar,
        direction: SignalDirection,
        regime: MarketRegime,
        trigger_quality_score: float,  # 0 to 20
        volume_ratio: float,           # Current vol / SMA20 vol
        avg_atr: float
    ) -> Tuple[float, Dict[str, float]]:
        breakdown: Dict[str, float] = {}

        # 1. VWAP Alignment (Max 20 pts)
        vwap_score = 0.0
        if bar.vwap:
            if direction == SignalDirection.BUY_CE and bar.close > bar.vwap:
                vwap_score = 20.0
            elif direction == SignalDirection.BUY_PE and bar.close < bar.vwap:
                vwap_score = 20.0
        breakdown["vwap_alignment"] = vwap_score

        # 2. EMA Alignment (Max 15 pts)
        ema_score = 0.0
        if bar.ema_20 and bar.ema_50:
            if direction == SignalDirection.BUY_CE and bar.ema_20 > bar.ema_50:
                ema_score = 15.0
            elif direction == SignalDirection.BUY_PE and bar.ema_20 < bar.ema_50:
                ema_score = 15.0
        breakdown["ema_alignment"] = ema_score

        # 3. Trigger Quality (Max 20 pts)
        breakdown["trigger_quality"] = min(20.0, max(0.0, trigger_quality_score))

        # 4. Volume Surge Confirmation (Max 15 pts)
        vol_score = 0.0
        if volume_ratio >= 1.8:
            vol_score = 15.0
        elif volume_ratio >= 1.3:
            vol_score = 10.0
        elif volume_ratio >= 1.0:
            vol_score = 5.0
        breakdown["volume_surge"] = vol_score

        # 5. RSI Confirmation (Max 10 pts)
        rsi_score = 0.0
        if bar.rsi_14:
            if direction == SignalDirection.BUY_CE and 55.0 <= bar.rsi_14 <= 75.0:
                rsi_score = 10.0
            elif direction == SignalDirection.BUY_PE and 25.0 <= bar.rsi_14 <= 45.0:
                rsi_score = 10.0
            elif (direction == SignalDirection.BUY_CE and bar.rsi_14 > 50.0) or \
                 (direction == SignalDirection.BUY_PE and bar.rsi_14 < 50.0):
                rsi_score = 5.0
        breakdown["rsi_momentum"] = rsi_score

        # 6. ATR / Volatility Expansion (Max 10 pts)
        atr_score = 0.0
        if bar.atr_14 and avg_atr > 0:
            atr_ratio = bar.atr_14 / avg_atr
            if 0.8 <= atr_ratio <= 2.0:
                atr_score = 10.0
            elif atr_ratio > 0.6:
                atr_score = 5.0
        breakdown["atr_volatility"] = atr_score

        # 7. Market Regime Confluence (Max 10 pts)
        regime_score = 0.0
        if direction == SignalDirection.BUY_CE and regime in (MarketRegime.STRONG_BULLISH, MarketRegime.WEAK_BULLISH):
            regime_score = 10.0 if regime == MarketRegime.STRONG_BULLISH else 6.0
        elif direction == SignalDirection.BUY_PE and regime in (MarketRegime.STRONG_BEARISH, MarketRegime.WEAK_BEARISH):
            regime_score = 10.0 if regime == MarketRegime.STRONG_BEARISH else 6.0
        breakdown["market_regime"] = regime_score

        total_score = round(sum(breakdown.values()), 1)
        return total_score, breakdown
