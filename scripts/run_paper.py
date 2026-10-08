import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import time
from datetime import datetime, timedelta
from core.constants import Underlying
from core.models import Bar
from paper_engine.runner import PaperTradingRunner
from data_engine.parquet_loader import ParquetDataLoader

def main():
    print("\n==================================================================")
    print("STARTING SHYAMEDGE LIVE PAPER-TRADING SESSION")
    print("Portfolio: ₹15,000 Virtual Capital | Max Open Positions: 1")
    print("Mode: PAPER TRADING ONLY (Real-Money Execution Disabled)")
    print("==================================================================\n")

    runner = PaperTradingRunner(underlying=Underlying.NIFTY50)
    runner.start()

    # In paper mode, we can ingest live feed or simulate real-time live playback
    loader = ParquetDataLoader()
    sample_bars = loader.load_or_generate_dataset(symbol=Underlying.NIFTY50, days=1, start_price=24800.0)

    print(f"[*] Ingesting session bars (Streaming 5-minute ticks)...")
    try:
        for b in sample_bars[:30]:
            res = runner.process_candle(b)
            active_info = f"Active: {res['active_position']}" if res.get('active_position') else "No Position"
            print(f"[{b.timestamp.strftime('%H:%M')}] Close: {b.close:<8.2f} | Regime: {res['regime']:<16} | Capital: ₹{res['capital']:<8.2f} | {active_info}")
            time.sleep(0.1)  # Simulated fast playback

        print("\n[*] Paper session simulation cycle complete.")
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user.")
    finally:
        runner.stop()

if __name__ == "__main__":
    main()
