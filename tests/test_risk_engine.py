from datetime import datetime, date
import pytest
from core.models import Position, Trade
from core.constants import StrategyID, Underlying, OptionType, PositionStatus
from core.exceptions import PositionLimitExceededException
from risk_engine.portfolio import VirtualPortfolio
from risk_engine.kill_switch import KillSwitchManager
from risk_engine.limits import RiskLimitsValidator
from core.models import Signal
from core.constants import SignalDirection, MarketRegime

def test_portfolio_single_position_limit():
    portfolio = VirtualPortfolio(initial_capital=15000.0)
    now = datetime(2026, 10, 8, 10, 0)

    can_open, _ = portfolio.can_open_position(now)
    assert can_open

    pos1 = Position(
        strategy_id=StrategyID.ORB,
        option_symbol="NIFTY26OCT25000CE",
        underlying=Underlying.NIFTY50,
        option_type=OptionType.CE,
        strike=25000.0,
        expiry=now.date(),
        quantity=65,
        entry_time=now,
        entry_price=50.0,
        current_price=50.0,
        stop_loss=42.5,
        target=65.0,
        status=PositionStatus.OPEN
    )
    portfolio.register_entry(pos1)

    # Attempting to open a second concurrent position must fail
    can_open_second, reason = portfolio.can_open_position(now)
    assert not can_open_second
    assert "POSITION_LIMIT_EXCEEDED" in reason

def test_daily_loss_circuit_breaker():
    portfolio = VirtualPortfolio(initial_capital=15000.0, max_daily_loss_pct=0.03)  # ₹450 limit
    now = datetime(2026, 10, 8, 11, 0)

    # Create a losing trade of ₹500
    trade = Trade(
        strategy_id=StrategyID.VWAP_EMA,
        underlying=Underlying.NIFTY50,
        option_symbol="NIFTY26OCT25000CE",
        expiry_date=now.date(),
        strike=25000.0,
        option_type=OptionType.CE,
        entry_time=now,
        entry_price=50.0,
        exit_time=now,
        exit_price=40.0,
        quantity=50,
        gross_pnl=-500.0,
        brokerage=40.0,
        stt=0.0,
        exchange_charges=0.0,
        gst=0.0,
        sebi_charges=0.0,
        stamp_duty=0.0,
        total_charges=40.0,
        slippage=10.0,
        net_pnl=-550.0,
        return_pct=-22.0,
        entry_reason="TEST",
        exit_reason="SL_HIT",
        signal_score=80.0,
        market_regime=MarketRegime.STRONG_BULLISH,
        holding_time_minutes=15
    )
    portfolio.register_exit(trade)

    # Circuit breaker must be triggered!
    assert portfolio.daily_loss_limit_hit
    can_open, reason = portfolio.can_open_position(now)
    assert not can_open
    assert "CIRCUIT_BREAKER_DAILY_LOSS_LIMIT_HIT" in reason

def test_kill_switch():
    portfolio = VirtualPortfolio(initial_capital=15000.0)
    validator = RiskLimitsValidator(portfolio=portfolio, kill_switch_active=True)

    sig = Signal(
        strategy_id=StrategyID.ORB,
        timestamp=datetime.now(),
        underlying=Underlying.NIFTY50,
        direction=SignalDirection.BUY_CE,
        signal_score=85.0,
        market_regime=MarketRegime.STRONG_BULLISH,
        underlying_price=25000.0,
        is_accepted=True
    )

    can_trade, reason = validator.can_execute_trade(sig, datetime.now())
    assert not can_trade
    assert reason == "KILL_SWITCH_ACTIVE"
