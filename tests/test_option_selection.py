from datetime import datetime, date
from core.constants import Underlying, OptionType
from option_engine.selector import OptionStrikeSelector
from option_engine.validator import OptionValidator

def test_atm_strike_rounding():
    # NIFTY step is 50
    assert OptionStrikeSelector.calculate_atm_strike(Underlying.NIFTY50, 24823.5) == 24800.0
    assert OptionStrikeSelector.calculate_atm_strike(Underlying.NIFTY50, 24827.0) == 24850.0

    # SENSEX step is 100
    assert OptionStrikeSelector.calculate_atm_strike(Underlying.SENSEX, 81440.0) == 81400.0
    assert OptionStrikeSelector.calculate_atm_strike(Underlying.SENSEX, 81460.0) == 81500.0

def test_itm_strike_selection():
    # At spot 25000:
    # 1-Strike ITM for CE is 24950
    # 1-Strike ITM for PE is 25050
    itm_ce = OptionStrikeSelector.select_strike(Underlying.NIFTY50, 25000.0, OptionType.CE, prefer_itm=True)
    assert itm_ce == 24950.0

    itm_pe = OptionStrikeSelector.select_strike(Underlying.NIFTY50, 25000.0, OptionType.PE, prefer_itm=True)
    assert itm_pe == 25050.0

def test_option_validation_capital_and_risk_budget():
    # Capital: ₹15,000, Max risk: ₹300
    # Case 1: Expensive option (Premium ₹250 on 65 Nifty = ₹16,250 > ₹15,000 capital) -> MUST REJECT
    is_valid, reason = OptionValidator.validate(
        premium=250.0,
        lot_size=65,
        available_capital=15000.0,
        max_trade_risk_inr=300.0,
        stop_loss_pct=0.15
    )
    assert not is_valid
    assert "EXCEEDS_TOTAL_CAPITAL" in reason

    # Case 2: Excessive Risk Budget (Premium ₹100, Cost = ₹6,500. 15% SL = ₹975 > ₹300 max risk) -> MUST REJECT
    is_valid_risk, reason_risk = OptionValidator.validate(
        premium=100.0,
        lot_size=65,
        available_capital=15000.0,
        max_trade_risk_inr=300.0,
        stop_loss_pct=0.15
    )
    assert not is_valid_risk
    assert "EXCEEDS_RISK_BUDGET" in reason_risk

    # Case 3: Valid contract (Premium ₹25, Cost = ₹1,625. 15% SL = ₹243.75 <= ₹300 max risk) -> MUST PASS
    is_valid_ok, reason_ok = OptionValidator.validate(
        premium=25.0,
        lot_size=65,
        available_capital=15000.0,
        max_trade_risk_inr=300.0,
        stop_loss_pct=0.15
    )
    assert is_valid_ok
    assert reason_ok is None
