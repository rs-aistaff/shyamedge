from typing import List, Optional

class StreamingRSI:
    """
    Online Wilder's 14-period Relative Strength Index calculation.
    """
    def __init__(self, period: int = 14):
        self.period = period
        self.prev_price: Optional[float] = None
        self.avg_gain: Optional[float] = None
        self.avg_loss: Optional[float] = None
        self.gains: List[float] = []
        self.losses: List[float] = []

    def update(self, price: float) -> float:
        if self.prev_price is None:
            self.prev_price = price
            return 50.0  # Neutral baseline on first candle

        change = price - self.prev_price
        gain = max(0.0, change)
        loss = max(0.0, -change)
        self.prev_price = price

        if self.avg_gain is None:
            self.gains.append(gain)
            self.losses.append(loss)
            if len(self.gains) < self.period:
                return 50.0
            else:
                self.avg_gain = sum(self.gains) / self.period
                self.avg_loss = sum(self.losses) / self.period
        else:
            self.avg_gain = (self.avg_gain * (self.period - 1) + gain) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + loss) / self.period

        if self.avg_loss == 0.0:
            return 100.0 if self.avg_gain > 0 else 50.0

        rs = self.avg_gain / self.avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return round(rsi, 2)

def compute_rsi_series(prices: List[float], period: int = 14) -> List[float]:
    """Computes RSI series across historical price series."""
    calc = StreamingRSI(period)
    return [calc.update(p) for p in prices]
