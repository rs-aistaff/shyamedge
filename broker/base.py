from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from core.models import Order, Position, Trade

class BrokerInterface(ABC):
    """
    Abstract interface for broker execution engines.
    Permits seamless swapping between PaperBroker and future LiveBroker.
    """
    @abstractmethod
    def buy(
        self,
        symbol: str,
        quantity: int,
        requested_price: float,
        stop_loss: float,
        target: float,
        **kwargs
    ) -> Order:
        """Executes a buy order."""
        pass

    @abstractmethod
    def sell(
        self,
        symbol: str,
        quantity: int,
        requested_price: float,
        reason: str,
        **kwargs
    ) -> Order:
        """Executes a sell order."""
        pass

    @abstractmethod
    def get_open_positions(self) -> List[Position]:
        """Returns list of currently active open positions."""
        pass
