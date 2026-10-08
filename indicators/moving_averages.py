from typing import List, Optional
import numpy as np

class StreamingEMA:
    """
    Incremental Exponential Moving Average for live tick/bar ingestion.
    """
    def __init__(self, period: int):
        self.period = period
        self.alpha = 2.0 / (period + 1.0)
        self.value: Optional[float] = None
        self._history: List[float] = []

    def update(self, price: float) -> float:
        if self.value is None:
            self._history.append(price)
            if len(self._history) < self.period:
                # Use running average until seed period is reached
                return sum(self._history) / len(self._history)
            else:
                self.value = sum(self._history) / len(self._history)
                return self.value
        else:
            self.value = self.alpha * price + (1.0 - self.alpha) * self.value
            return self.value

def compute_ema_series(prices: List[float], period: int) -> List[float]:
    """Computes EMA series over a chronological price list."""
    if not prices:
        return []
    ema_calc = StreamingEMA(period)
    return [ema_calc.update(p) for p in prices]

def compute_sma_series(prices: List[float], period: int) -> List[float]:
    """Computes Simple Moving Average (SMA) series."""
    result = []
    window = []
    for p in prices:
        window.append(p)
        if len(window) > period:
            window.pop(0)
        result.append(sum(window) / len(window))
    return result
