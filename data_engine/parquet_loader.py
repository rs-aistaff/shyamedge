from datetime import datetime, timedelta, time
from typing import List, Optional
from pathlib import Path
import numpy as np
import pandas as pd
from core.models import Bar
from core.constants import Underlying

class ParquetDataLoader:
    """
    Loads historical 5-minute bars from Parquet/CSV data store,
    or generates realistic synthetic market datasets for testing.
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_or_generate_dataset(
        self,
        symbol: Underlying = Underlying.NIFTY50,
        days: int = 30,
        start_price: float = 24500.0
    ) -> List[Bar]:
        """
        Loads cached dataset or synthesizes realistic intraday 5-min candles
        (09:15 to 15:30 IST) for backtesting and algorithm verification.
        """
        file_path = self.data_dir / f"{symbol.value}_5m_{days}d.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            bars = []
            for _, row in df.iterrows():
                bars.append(Bar(
                    timestamp=pd.to_datetime(row["timestamp"]),
                    symbol=symbol,
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=int(row["volume"]),
                    timeframe="5m"
                ))
            return bars

        # Generate realistic intraday bars with market microstructure
        bars = []
        current_date = datetime.now().date() - timedelta(days=days)
        price = start_price

        # Fixed seed for consistent reproducible backtests across cycles
        np.random.seed(42)

        # 5-min intervals from 09:15 to 15:30 is 75 bars per day
        for d in range(days):
            trade_date = current_date + timedelta(days=d)
            if trade_date.weekday() >= 5:  # Skip weekends
                continue

            session_open = datetime.combine(trade_date, time(9, 15))
            
            # Daily gap between -0.4% and +0.4%
            daily_gap_pct = np.random.normal(0.0005, 0.0035)
            price = round(price * (1.0 + daily_gap_pct), 2)
            day_open_price = price

            # Determine day regime: 40% Trending (Bull/Bear), 35% Mean Reversion, 25% Breakout
            day_type_rand = np.random.rand()
            if day_type_rand < 0.22:
                # Strong Bull Trend day
                day_trend_drift = 0.00028
                persistence = 0.32
            elif day_type_rand < 0.44:
                # Strong Bear Trend day
                day_trend_drift = -0.00028
                persistence = 0.32
            elif day_type_rand < 0.70:
                # Mean-reverting / Rangebound day (mean reversion pull to day open)
                day_trend_drift = 0.0
                persistence = -0.15
            else:
                # Expansion breakout day
                day_trend_drift = 0.00015 * (1 if np.random.rand() > 0.5 else -1)
                persistence = 0.25

            prev_return = 0.0

            for b in range(75):
                bar_time = session_open + timedelta(minutes=b * 5)
                
                # U-shaped intraday volume curve typical of NSE / BSE
                # High in opening hour (b: 0-15), low midday (b: 25-45), high in closing hour (b: 55-74)
                if b < 12:  # 09:15 - 10:15
                    vol_mult = 1.6 + 0.4 * (12 - b) / 12.0
                elif b > 55:  # 13:50 - 15:30
                    vol_mult = 1.3 + 0.6 * (b - 55) / 20.0
                elif 24 <= b <= 45:  # 11:15 - 13:00 (midday lull)
                    vol_mult = 0.65
                else:
                    vol_mult = 1.0

                # Return model: trend drift + autoregressive momentum + random shock
                shock = np.random.normal(0.0, 0.00085)
                ret = day_trend_drift + (persistence * prev_return) + shock
                
                # Mean reversion pull if rangebound day
                if day_trend_drift == 0.0 and abs(price - day_open_price) / day_open_price > 0.006:
                    ret -= 0.0004 * np.sign(price - day_open_price)

                prev_return = ret

                open_p = price
                close_p = round(open_p * (1.0 + ret), 2)
                wick_high = abs(np.random.normal(0.0, 0.0005))
                wick_low = abs(np.random.normal(0.0, 0.0005))
                high_p = round(max(open_p, close_p) * (1.0 + wick_high), 2)
                low_p = round(min(open_p, close_p) * (1.0 - wick_low), 2)
                
                base_vol = np.random.gamma(shape=5.0, scale=12000)
                vol = int(max(1000, base_vol * vol_mult))

                price = close_p
                bars.append(Bar(
                    timestamp=bar_time,
                    symbol=symbol,
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=vol,
                    timeframe="5m"
                ))

        # Save to parquet for fast subsequent loads
        records = [
            {
                "timestamp": b.timestamp,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume
            }
            for b in bars
        ]
        df = pd.DataFrame(records)
        df.to_parquet(file_path, index=False)

        return bars
