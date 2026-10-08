from datetime import datetime, date
from typing import List, Dict, Any, Optional
import numpy as np

class IntradayVWAP:
    """
    Computes cumulative Volume-Weighted Average Price (VWAP) for intraday sessions.
    Automatically resets when a new calendar date begins.
    """
    def __init__(self):
        self.current_date: Optional[date] = None
        self.cum_typical_volume: float = 0.0
        self.cum_volume: float = 0.0

    def update(self, dt: datetime, high: float, low: float, close: float, volume: float) -> float:
        """
        Updates the running intraday VWAP with the latest candle.
        """
        bar_date = dt.date()
        if self.current_date != bar_date:
            # New trading day session reset
            self.current_date = bar_date
            self.cum_typical_volume = 0.0
            self.cum_volume = 0.0

        typical_price = (high + low + close) / 3.0
        # Protect against zero volume bars (e.g. illiquid or index synthetic)
        vol = max(volume, 1.0)

        self.cum_typical_volume += typical_price * vol
        self.cum_volume += vol

        return self.cum_typical_volume / self.cum_volume

def compute_vwap_series(dates: List[datetime], highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> List[float]:
    """
    Vector-like helper to compute VWAP series across chronological candles.
    """
    vwap_calc = IntradayVWAP()
    result = []
    for dt, h, l, c, v in zip(dates, highs, lows, closes, volumes):
        result.append(vwap_calc.update(dt, h, l, c, v))
    return result
