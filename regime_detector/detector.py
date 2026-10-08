from typing import List, Optional
from core.constants import MarketRegime
from core.models import Bar

class MarketRegimeDetector:
    """
    Classifies the underlying index into objective market regimes
    to eliminate options premium decay in choppy or sideways markets.
    """
    def __init__(self, atr_window: int = 50):
        self.atr_history: List[float] = []
        self.atr_window = atr_window

    def detect(self, bar: Bar, ema_20_prev: Optional[float] = None) -> MarketRegime:
        """
        Evaluates current candle features to output market regime.
        """
        if (bar.vwap is None or bar.ema_20 is None or
            bar.ema_50 is None or bar.rsi_14 is None or bar.atr_14 is None):
            return MarketRegime.UNCLEAR

        self.atr_history.append(bar.atr_14)
        if len(self.atr_history) > self.atr_window:
            self.atr_history.pop(0)

        avg_atr = sum(self.atr_history) / len(self.atr_history)

        # Volatility extremes
        if bar.atr_14 > 2.2 * avg_atr:
            return MarketRegime.HIGH_VOLATILITY
        if bar.atr_14 < 0.45 * avg_atr:
            return MarketRegime.LOW_VOLATILITY

        # Check for Sideways / Choppy compression (Dangerous for option buyers)
        ema_spread_pct = abs(bar.ema_20 - bar.ema_50) / bar.close
        price_vwap_spread_pct = abs(bar.close - bar.vwap) / bar.close

        if ema_spread_pct < 0.0008 and price_vwap_spread_pct < 0.0010 and 45.0 <= bar.rsi_14 <= 55.0:
            return MarketRegime.SIDEWAYS

        # Trend evaluations
        ema_slope_up = (bar.ema_20 > ema_20_prev) if ema_20_prev is not None else True
        ema_slope_down = (bar.ema_20 < ema_20_prev) if ema_20_prev is not None else True

        # Bullish Regimes
        if bar.close > bar.vwap and bar.ema_20 > bar.ema_50:
            if bar.rsi_14 >= 55.0 and ema_slope_up:
                return MarketRegime.STRONG_BULLISH
            else:
                return MarketRegime.WEAK_BULLISH

        # Bearish Regimes
        if bar.close < bar.vwap and bar.ema_20 < bar.ema_50:
            if bar.rsi_14 <= 45.0 and ema_slope_down:
                return MarketRegime.STRONG_BEARISH
            else:
                return MarketRegime.WEAK_BEARISH

        return MarketRegime.SIDEWAYS
