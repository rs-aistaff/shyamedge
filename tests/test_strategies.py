from datetime import datetime, date, time
from core.models import Bar
from core.constants import Underlying, StrategyID, SignalDirection, MarketRegime
from strategies.signal_scorer import SignalScorer
from strategies.orb_v1 import ORBStrategy
from strategies.vwap_ema_v1 import VWAPEMAStrategy

def test_signal_scorer_threshold():
    bar = Bar(
        timestamp=datetime(2026, 10, 8, 10, 0),
        symbol=Underlying.NIFTY50,
        open=24800, high=24850, low=24790, close=24840,
        volume=50000,
        vwap=24810.0,
        ema_20=24820.0,
        ema_50=24800.0,
        rsi_14=62.0,
        atr_14=35.0
    )

    # Bullish setup aligned with strong trend
    score, breakdown = SignalScorer.score(
        bar=bar,
        direction=SignalDirection.BUY_CE,
        regime=MarketRegime.STRONG_BULLISH,
        trigger_quality_score=18.0,
        volume_ratio=1.5,
        avg_atr=35.0
    )

    assert score >= 75.0  # Must qualify as valid candidate
    assert breakdown["vwap_alignment"] == 20.0
    assert breakdown["ema_alignment"] == 15.0

def test_orb_strategy_rejection_in_sideways_regime():
    strat = ORBStrategy()
    bar = Bar(
        timestamp=datetime(2026, 10, 8, 9, 45),
        symbol=Underlying.NIFTY50,
        open=24800, high=24860, low=24790, close=24855,
        volume=50000,
        vwap=24810.0,
        rsi_14=60.0,
        atr_14=30.0
    )

    # In SIDEWAYS regime, ORB must reject signal to prevent theta decay
    sig = strat.evaluate_candle(
        bar=bar,
        regime=MarketRegime.SIDEWAYS,
        avg_volume_20=30000,
        avg_atr_14=30.0,
        or_high=24850.0,
        or_low=24800.0,
        is_or_established=True
    )
    assert sig is None
