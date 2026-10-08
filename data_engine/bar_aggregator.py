from datetime import datetime, timedelta
from typing import Optional, List
from core.models import Bar
from core.constants import Underlying

class BarAggregator5Min:
    """
    Aggregates incoming 1-minute bars into completed 5-minute candles.
    Only emits a completed 5-minute bar when the interval completes,
    preventing lookahead bias.
    """
    def __init__(self, symbol: Underlying):
        self.symbol = symbol
        self.current_bucket_start: Optional[datetime] = None
        self.open_p: Optional[float] = None
        self.high_p: Optional[float] = None
        self.low_p: Optional[float] = None
        self.close_p: Optional[float] = None
        self.total_volume: int = 0
        self.accumulated_bars = 0

    def add_1m_bar(self, dt: datetime, open_p: float, high_p: float, low_p: float, close_p: float, volume: int) -> Optional[Bar]:
        # Determine 5-minute bucket starting boundary
        minute = (dt.minute // 5) * 5
        bucket_start = dt.replace(minute=minute, second=0, microsecond=0)

        completed_bar: Optional[Bar] = None

        if self.current_bucket_start is not None and bucket_start > self.current_bucket_start:
            # Emit completed bar from prior bucket
            completed_bar = Bar(
                timestamp=self.current_bucket_start + timedelta(minutes=5),
                symbol=self.symbol,
                open=self.open_p,
                high=self.high_p,
                low=self.low_p,
                close=self.close_p,
                volume=self.total_volume,
                timeframe="5m"
            )
            # Reset for new bucket
            self.current_bucket_start = bucket_start
            self.open_p = open_p
            self.high_p = high_p
            self.low_p = low_p
            self.close_p = close_p
            self.total_volume = volume
            self.accumulated_bars = 1
        else:
            if self.current_bucket_start is None:
                self.current_bucket_start = bucket_start
                self.open_p = open_p
                self.high_p = high_p
                self.low_p = low_p
                self.close_p = close_p
                self.total_volume = volume
                self.accumulated_bars = 1
            else:
                self.high_p = max(self.high_p, high_p)
                self.low_p = min(self.low_p, low_p)
                self.close_p = close_p
                self.total_volume += volume
                self.accumulated_bars += 1

        return completed_bar
