from abc import ABC, abstractmethod
from typing import List, Generator
from core.models import Bar

class BaseDataEngine(ABC):
    """Abstract interface for historical and live market data ingestion."""

    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str = "5m", limit: int = 500) -> List[Bar]:
        """Fetches historical bars."""
        pass

    @abstractmethod
    def stream_bars(self, symbol: str) -> Generator[Bar, None, None]:
        """Streams chronological bars."""
        pass
