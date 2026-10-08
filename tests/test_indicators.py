from datetime import datetime, date, time
from indicators.vwap import IntradayVWAP
from indicators.moving_averages import StreamingEMA
from indicators.momentum import StreamingRSI
from indicators.volatility import StreamingATR
from indicators.levels import OpeningRangeTracker
from core.models import Bar
from core.constants import Underlying

def test_vwap_calculation_and_session_reset():
    vwap = IntradayVWAP()
    dt1 = datetime(2026, 10, 8, 9, 15)
    # Candle 1: H=105, L=95, C=100 (Typical = 100), Vol = 1000
    res1 = vwap.update(dt1, 105, 95, 100, 1000)
    assert round(res1, 2) == 100.0

    # Candle 2: H=115, L=105, C=110 (Typical = 110), Vol = 1000
    # Cum vol = 2000, Cum typical vol = 100*1000 + 110*1000 = 210,000 -> VWAP = 105
    res2 = vwap.update(datetime(2026, 10, 8, 9, 20), 115, 105, 110, 1000)
    assert round(res2, 2) == 105.0

    # Next Day Session Reset (2026-10-09)
    dt_next_day = datetime(2026, 10, 9, 9, 15)
    res_new_day = vwap.update(dt_next_day, 205, 195, 200, 500)
    assert round(res_new_day, 2) == 200.0

def test_streaming_ema():
    ema = StreamingEMA(period=5)
    # Seed values: [10, 10, 10, 10, 10]
    for _ in range(5):
        val = ema.update(10.0)
    assert round(val, 2) == 10.0

    # Update with 16.0: alpha = 2/(5+1) = 2/6 = 0.3333
    # New EMA = 0.3333 * 16 + 0.6667 * 10 = 5.333 + 6.667 = 12.0
    val2 = ema.update(16.0)
    assert round(val2, 2) == 12.0

def test_streaming_rsi_bounds():
    rsi = StreamingRSI(period=14)
    prices = [100 + i for i in range(30)]  # Monotonically increasing
    final_rsi = 50.0
    for p in prices:
        final_rsi = rsi.update(p)
    assert final_rsi > 80.0  # Strong bullish momentum

def test_streaming_atr():
    atr = StreamingATR(period=14)
    # 20 identical candles with Range = 10
    final_atr = 0.0
    for _ in range(20):
        final_atr = atr.update(high=110.0, low=100.0, close=105.0)
    assert round(final_atr, 1) == 10.0

def test_opening_range_tracker():
    tracker = OpeningRangeTracker()
    day = date(2026, 10, 8)

    # 09:15 bar (H=100, L=90)
    b1 = Bar(timestamp=datetime.combine(day, time(9, 15)), symbol=Underlying.NIFTY50, open=95, high=100, low=90, close=98, volume=100)
    h, l, ready = tracker.update(b1)
    assert not ready
    assert h == 100 and l == 90

    # 09:20 bar (H=105, L=85)
    b2 = Bar(timestamp=datetime.combine(day, time(9, 20)), symbol=Underlying.NIFTY50, open=98, high=105, low=85, close=102, volume=100)
    h, l, ready = tracker.update(b2)
    assert not ready
    assert h == 105 and l == 85

    # 09:30 bar (Range is established)
    b3 = Bar(timestamp=datetime.combine(day, time(9, 30)), symbol=Underlying.NIFTY50, open=102, high=104, low=95, close=103, volume=100)
    h, l, ready = tracker.update(b3)
    assert ready
    assert h == 105 and l == 85
