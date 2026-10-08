from datetime import datetime
from risk_engine.portfolio import VirtualPortfolio
from broker.paper_broker import PaperBroker
from core.models import Signal
from core.constants import Underlying, StrategyID, SignalDirection, MarketRegime, OrderStatus

def test_paper_broker_execution_with_slippage():
    portfolio = VirtualPortfolio(initial_capital=15000.0)
    broker = PaperBroker(portfolio=portfolio, slippage_pct=0.005)  # 0.5% adverse slippage

    sig = Signal(
        strategy_id=StrategyID.ORB,
        timestamp=datetime.utcnow(),
        underlying=Underlying.NIFTY50,
        direction=SignalDirection.BUY_CE,
        signal_score=82.0,
        market_regime=MarketRegime.STRONG_BULLISH,
        underlying_price=24800.0,
        is_accepted=True
    )

    # Buy 65 qty @ requested 100.0
    # Slippage: 100 * 0.005 = 0.50 -> Fill = 100.50
    order = broker.buy(
        symbol="NIFTY26OCT24800CE",
        quantity=65,
        requested_price=100.0,
        stop_loss=85.0,
        target=130.0,
        signal=sig
    )

    assert order.status == OrderStatus.FILLED
    assert order.executed_price == 100.50
    assert broker.portfolio.active_position is not None
    assert broker.portfolio.active_position.entry_price == 100.50

    # Sell 65 qty @ requested 120.0
    # Slippage: 120 * 0.005 = 0.60 -> Fill = 119.40
    exit_order = broker.sell(
        symbol="NIFTY26OCT24800CE",
        quantity=65,
        requested_price=120.0,
        reason="TARGET_HIT"
    )

    assert exit_order.status == OrderStatus.FILLED
    assert exit_order.executed_price == 119.40
    # Active position should now be closed
    assert broker.portfolio.active_position is None
    # Net PnL must be positive, but less than gross PnL due to statutory charges + slippage
    assert broker.portfolio.current_capital > 15000.0
