from typing import List, Optional

class StreamingATR:
    """
    Online Wilder's 14-period Average True Range calculation.
    """
    def __init__(self, period: int = 14):
        self.period = period
        self.prev_close: Optional[float] = None
        self.atr: Optional[float] = None
        self.tr_history: List[float] = []

    def update(self, high: float, low: float, close: float) -> float:
        if self.prev_close is None:
            tr = high - low
        else:
            tr = max(high - low, abs(high - self.prev_close), abs(low - self.prev_close))
        self.prev_close = close

        if self.atr is None:
            self.tr_history.append(tr)
            if len(self.tr_history) < self.period:
                return sum(self.tr_history) / len(self.tr_history)
            else:
                self.atr = sum(self.tr_history) / self.period
                return round(self.atr, 2)
        else:
            self.atr = (self.atr * (self.period - 1) + tr) / self.period
            return round(self.atr, 2)

def compute_atr_series(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
    """Computes ATR series across historical OHLC bars."""
    calc = StreamingATR(period)
    return [calc.update(h, l, c) for h, l, c in zip(highs, lows, closes)]
