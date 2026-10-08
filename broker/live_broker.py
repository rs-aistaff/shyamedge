from broker.base import BrokerInterface
from core.models import Order, Position
from typing import List

class LiveBroker(BrokerInterface):
    """
    Live broker adapter placeholder.
    STRICTLY DISABLED IN COMPLIANCE WITH SYSTEM SPECIFICATIONS.
    """
    def __init__(self, *args, **kwargs):
        raise PermissionError(
            "CRITICAL SECURITY SAFEGUARD: LIVE TRADING IS PERMANENTLY DISABLED IN THIS PHASE. "
            "SYSTEM OPERATES UNDER STRICT PAPER-TRADING ONLY (₹15,000 VIRTUAL CAPITAL)."
        )

    def buy(self, *args, **kwargs) -> Order:
        raise PermissionError("LIVE ORDERS DISABLED.")

    def sell(self, *args, **kwargs) -> Order:
        raise PermissionError("LIVE ORDERS DISABLED.")

    def get_open_positions(self) -> List[Position]:
        return []
