from core.constants import Underlying, LOT_SIZES

class PositionSizer:
    """
    Computes strict fixed 1-lot position sizing for ₹15,000 virtual portfolio.
    Guarantees no martingale, no averaging down, and no size escalation after losses.
    """
    @classmethod
    def calculate_quantity(cls, underlying: Underlying) -> int:
        # Fixed 1 lot to strictly adhere to ₹15,000 portfolio boundary
        return LOT_SIZES[underlying]
