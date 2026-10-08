from config.cost_model import CostCalculator

def test_cost_calculator_itemization():
    # Buy 1 lot NIFTY (65 quantity) @ 100, Sell @ 130
    costs = CostCalculator.calculate(
        buy_price=100.0,
        sell_price=130.0,
        quantity=65,
        slippage_pct=0.004,
        tick_size=0.05
    )

    # Turnovers
    assert costs.turnover_buy == 6500.0
    assert costs.turnover_sell == 8450.0

    # Brokerage: 20 buy + 20 sell = 40.0
    assert costs.brokerage == 40.0

    # STT: 0.1% on sell turnover (8450 * 0.001 = 8.45)
    assert costs.stt == 8.45

    # Stamp duty: 0.003% on buy turnover (6500 * 0.00003 = 0.20)
    assert costs.stamp_duty == 0.20

    # Total statutory charges > brokerage + stt
    assert costs.total_statutory_charges > 48.0

    # Slippage exists and is positive
    assert costs.total_slippage > 0.0
    assert costs.total_cost == round(costs.total_statutory_charges + costs.total_slippage, 2)
