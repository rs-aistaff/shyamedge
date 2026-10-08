from dataclasses import dataclass
import math

@dataclass
class TransactionCosts:
    turnover_buy: float
    turnover_sell: float
    brokerage: float
    stt: float
    exchange_charges: float
    sebi_charges: float
    stamp_duty: float
    gst: float
    total_statutory_charges: float
    slippage_buy: float
    slippage_sell: float
    total_slippage: float
    total_cost: float

class CostCalculator:
    """
    Computes exact statutory, exchange, regulatory, brokerage, and slippage costs
    for Indian Index Options Trading based on current (2025-2026) Finance Act rules.
    """
    # Rates
    BROKERAGE_PER_ORDER = 20.0  # ₹20 per executed order
    STT_SELL_RATE = 0.001       # 0.1% on sell side option premium turnover
    EXCHANGE_TURNOVER_RATE = 0.000495  # NSE/BSE ~0.0495%
    SEBI_TURNOVER_RATE = 0.000001     # ₹10 per crore (0.0001%)
    STAMP_DUTY_BUY_RATE = 0.00003     # 0.003% on buy side premium turnover
    GST_RATE = 0.18                    # 18% on (Brokerage + Exchange + SEBI)

    @classmethod
    def calculate(
        cls,
        buy_price: float,
        sell_price: float,
        quantity: int,
        slippage_pct: float = 0.004,
        tick_size: float = 0.05
    ) -> TransactionCosts:
        """
        Calculates itemized round-trip transaction costs and adverse slippage.
        """
        # Turnovers (Premium * Qty)
        turnover_buy = round(buy_price * quantity, 2)
        turnover_sell = round(sell_price * quantity, 2)
        total_turnover = turnover_buy + turnover_sell

        # 1. Brokerage
        brokerage = cls.BROKERAGE_PER_ORDER * 2.0  # ₹40 round trip

        # 2. STT (Securities Transaction Tax) - 0.1% on sell premium
        stt = round(turnover_sell * cls.STT_SELL_RATE, 2)

        # 3. Exchange Turnover Charges
        exchange_charges = round(total_turnover * cls.EXCHANGE_TURNOVER_RATE, 2)

        # 4. SEBI Turnover Charges
        sebi_charges = round(total_turnover * cls.SEBI_TURNOVER_RATE, 2)

        # 5. Stamp Duty (Buy side only)
        stamp_duty = round(turnover_buy * cls.STAMP_DUTY_BUY_RATE, 2)

        # 6. GST (18% on Brokerage + Exchange + SEBI)
        gst = round((brokerage + exchange_charges + sebi_charges) * cls.GST_RATE, 2)

        total_statutory = round(brokerage + stt + exchange_charges + sebi_charges + stamp_duty + gst, 2)

        # 7. Adverse Slippage (Simulated market order impact)
        # Buyer pays slightly higher, seller receives slightly lower
        slip_buy_per_unit = max(tick_size, round(buy_price * slippage_pct, 2))
        slip_sell_per_unit = max(tick_size, round(sell_price * slippage_pct, 2))

        slippage_buy = round(slip_buy_per_unit * quantity, 2)
        slippage_sell = round(slip_sell_per_unit * quantity, 2)
        total_slippage = round(slippage_buy + slippage_sell, 2)

        total_cost = round(total_statutory + total_slippage, 2)

        return TransactionCosts(
            turnover_buy=turnover_buy,
            turnover_sell=turnover_sell,
            brokerage=brokerage,
            stt=stt,
            exchange_charges=exchange_charges,
            sebi_charges=sebi_charges,
            stamp_duty=stamp_duty,
            gst=gst,
            total_statutory_charges=total_statutory,
            slippage_buy=slippage_buy,
            slippage_sell=slippage_sell,
            total_slippage=total_slippage,
            total_cost=total_cost
        )
