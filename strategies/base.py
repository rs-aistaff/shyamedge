from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
from core.constants import StrategyID, SignalDirection, MarketRegime
from core.models import Bar, Signal, Position

class BaseStrategy(ABC):
    """
    Abstract Base Class for all ShyamEdge algorithmic strategies.
    Ensures consistent signal interfaces and rigorous exit rules.
    """
    def __init__(self, strategy_id: StrategyID, version: str = "v1.0"):
        self.strategy_id = strategy_id
        self.version = version

    @abstractmethod
    def evaluate_candle(
        self,
        bar: Bar,
        regime: MarketRegime,
        avg_volume_20: float,
        avg_atr_14: float,
        **kwargs
    ) -> Optional[Signal]:
        """
        Evaluates a newly closed 5-minute candle and returns a Signal if valid,
        or None if no actionable setup exists.
        """
        pass

    @abstractmethod
    def check_exit(
        self,
        position: Position,
        current_option_price: float,
        underlying_bar: Bar
    ) -> Tuple[bool, str]:
        """
        Evaluates active position for exit conditions:
        Returns: (should_exit: bool, exit_reason: str)
        """
        pass
