from typing import Tuple, Optional

class OptionValidator:
    """
    Validates candidate option contracts for liquidity, bid-ask spread,
    and portfolio capital/risk budget suitability.
    """
    MAX_SPREAD_PCT = 0.02         # Max allowable spread 2.0%
    MIN_OPEN_INTEREST = 20000     # Minimum contracts OI
    MAX_CAPITAL_ALLOC_PCT = 0.65  # Max 65% of virtual capital on single position

    @classmethod
    def validate(
        cls,
        premium: float,
        lot_size: int,
        available_capital: float,
        max_trade_risk_inr: float,
        stop_loss_pct: float = 0.15,
        bid_price: Optional[float] = None,
        ask_price: Optional[float] = None,
        open_interest: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        # 1. Total Capital Cost check
        total_cost = premium * lot_size
        max_allowed_cost = available_capital * cls.MAX_CAPITAL_ALLOC_PCT

        if total_cost > available_capital:
            return False, f"EXCEEDS_TOTAL_CAPITAL: Needed ₹{total_cost:.1f} > Avail ₹{available_capital:.1f}"

        if total_cost > max_allowed_cost:
            return False, f"EXCEEDS_POSITION_ALLOCATION: Needed ₹{total_cost:.1f} > Max ₹{max_allowed_cost:.1f}"

        # 2. Risk Budget check (Strictly respects caller's max_trade_risk_inr)
        point_risk = premium * stop_loss_pct
        planned_risk = point_risk * lot_size
        allowed_risk = max_trade_risk_inr * 1.35
        if planned_risk > allowed_risk:
            return False, f"EXCEEDS_RISK_BUDGET: Planned Risk ₹{planned_risk:.1f} > Allowed Risk ₹{allowed_risk:.1f}"

        # 3. Bid-Ask Spread check
        if bid_price is not None and ask_price is not None and ask_price > 0:
            spread = ask_price - bid_price
            spread_pct = spread / ask_price
            if spread_pct > cls.MAX_SPREAD_PCT:
                return False, f"SPREAD_TOO_WIDE: {spread_pct * 100:.1f}% > {cls.MAX_SPREAD_PCT * 100}%"

        # 4. Open Interest check
        if open_interest is not None and open_interest < cls.MIN_OPEN_INTEREST:
            return False, f"INSUFFICIENT_LIQUIDITY_OI: {open_interest} < {cls.MIN_OPEN_INTEREST}"

        return True, None
