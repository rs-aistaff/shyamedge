from datetime import datetime, date, time
from typing import Optional, List, Tuple
from core.models import Bar

class OpeningRangeTracker:
    """
    Captures the Opening Range (09:15 - 09:30 IST) for intraday breakout detection.
    """
    def __init__(self):
        self.current_date: Optional[date] = None
        self.or_high: Optional[float] = None
        self.or_low: Optional[float] = None
        self.is_established: bool = False

    def update(self, bar: Bar) -> Tuple[Optional[float], Optional[float], bool]:
        bar_date = bar.timestamp.date()
        bar_time = bar.timestamp.time()

        if self.current_date != bar_date:
            self.current_date = bar_date
            self.or_high = None
            self.or_low = None
            self.is_established = False

        # During 09:15:00 to 09:29:59 (first three 5-min bars)
        if time(9, 15) <= bar_time < time(9, 30):
            if self.or_high is None or bar.high > self.or_high:
                self.or_high = bar.high
            if self.or_low is None or bar.low < self.or_low:
                self.or_low = bar.low

        if bar_time >= time(9, 30) and self.or_high is not None and self.or_low is not None:
            self.is_established = True

        return self.or_high, self.or_low, self.is_established

class KeyLevelsTracker:
    """
    Tracks Previous Day High/Low (PDH/PDL) and Donchian Swing Levels.
    """
    def __init__(self, swing_period: int = 20):
        self.swing_period = swing_period
        self.highs_window: List[float] = []
        self.lows_window: List[float] = []

    def update(self, high: float, low: float) -> Tuple[float, float]:
        self.highs_window.append(high)
        self.lows_window.append(low)
        if len(self.highs_window) > self.swing_period:
            self.highs_window.pop(0)
            self.lows_window.pop(0)

        # Exclude the current candle from swing high/low calculation to prevent lookahead
        if len(self.highs_window) > 1:
            swing_high = max(self.highs_window[:-1])
            swing_low = min(self.lows_window[:-1])
        else:
            swing_high = high
            swing_low = low

        return swing_high, swing_low
