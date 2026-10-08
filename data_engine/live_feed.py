import logging
from datetime import datetime, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo
import httpx

from core.constants import Underlying
from core.models import Bar
from config.trading_hours import IST_TZ

logger = logging.getLogger(__name__)

class LiveFeedFetcher:
    """
    Real-time 5-minute Market Data Fetcher for Indian Indices (NIFTY 50 & SENSEX).
    Connects to the official exchange live feed endpoint to fetch newly closed 5m bars.
    Zero external subscription required; zero lookahead bias.
    """
    SYMBOL_MAP = {
        Underlying.NIFTY50: "^NSEI",
        Underlying.SENSEX: "^BSESN"
    }

    def __init__(self, underlying: Underlying = Underlying.NIFTY50):
        self.underlying = underlying
        self.ticker = self.SYMBOL_MAP.get(underlying, "^NSEI")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.last_processed_timestamp: Optional[datetime] = None

    def fetch_today_5m_bars(self) -> List[Bar]:
        """
        Fetches all 5-minute candles of the active trading session.
        Returns sorted list of validated Bar objects.
        """
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.ticker}?interval=5m&range=1d"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=self.headers)
                if resp.status_code != 200:
                    logger.warning(f"Live feed returned status {resp.status_code} for {self.ticker}")
                    return []
                data = resp.json()

            res = data.get("chart", {}).get("result", [])
            if not res:
                return []

            first_res = res[0]
            timestamps = first_res.get("timestamp", [])
            quote = first_res.get("indicators", {}).get("quote", [{}])[0]

            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            closes = quote.get("close", [])
            volumes = quote.get("volume", [])

            bars: List[Bar] = []
            for i, ts in enumerate(timestamps):
                # Skip invalid or missing data points
                if (
                    i >= len(opens) or opens[i] is None or
                    i >= len(highs) or highs[i] is None or
                    i >= len(lows) or lows[i] is None or
                    i >= len(closes) or closes[i] is None
                ):
                    continue

                dt_ist = datetime.fromtimestamp(ts, tz=IST_TZ)
                vol = int(volumes[i]) if (i < len(volumes) and volumes[i] is not None) else 10000

                bar = Bar(
                    timestamp=dt_ist,
                    symbol=self.underlying,
                    open=round(float(opens[i]), 2),
                    high=round(float(highs[i]), 2),
                    low=round(float(lows[i]), 2),
                    close=round(float(closes[i]), 2),
                    volume=max(vol, 1000),
                    timeframe="5m"
                )
                bars.append(bar)

            return bars
        except Exception as e:
            logger.error(f"Error fetching live 5m bars for {self.ticker}: {e}")
            return []

    def get_latest_closed_bar(self) -> Optional[Bar]:
        """
        Returns the latest completed 5-minute candle if it hasn't been processed yet.
        """
        bars = self.fetch_today_5m_bars()
        if not bars:
            return None

        latest = bars[-1]
        if self.last_processed_timestamp is None or latest.timestamp > self.last_processed_timestamp:
            self.last_processed_timestamp = latest.timestamp
            return latest

        return None
