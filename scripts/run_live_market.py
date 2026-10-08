import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import time
import argparse
from datetime import datetime, timedelta, time as dtime
from core.constants import Underlying
from config.trading_hours import MarketSessionManager, IST_TZ
from paper_engine.live_market_daemon import LiveMarketDaemon
from data_engine.parquet_loader import ParquetDataLoader

def main():
    parser = argparse.ArgumentParser(description="ShyamEdge Morning Live Market Paper-Trading Runner")
    parser.add_argument("--symbol", type=str, default="SENSEX", choices=["SENSEX", "NIFTY50"])
    parser.add_argument("--simulate", action="store_true", help="Run simulated live clock playback (for off-hours/weekend testing)")
    args = parser.parse_args()

    symbol = Underlying(args.symbol)

    print("\n==================================================================")
    print("SHYAMEDGE MORNING LIVE PAPER-TRADING DAEMON")
    print(f"Target Underlying : {symbol.value}")
    print(f"Virtual Portfolio : ₹15,000.00 Capital | Max Loss: ₹450.00 (3%)")
    print("Execution Mode    : STRICT PAPER TRADING (Real-Money Execution Disabled)")
    print("Timezone          : IST (Asia/Kolkata)")
    print("==================================================================\n")

    daemon = LiveMarketDaemon(underlying=symbol, is_simulation=args.simulate)

    # Determine whether market is currently active or simulation requested
    now_ist = datetime.now(IST_TZ)
    is_live_now = MarketSessionManager.is_market_open(now_ist)

    if not is_live_now or args.simulate:
        if not args.simulate:
            print(f"[*] Note: Indian market is currently closed ({now_ist.strftime('%H:%M:%S IST')}).")
            print("[*] Starting in LIVE SIMULATION PLAYBACK MODE to demonstrate real-time activity on-point...")
        else:
            print("[*] Starting in LIVE SIMULATION PLAYBACK MODE...")

        loader = ParquetDataLoader()
        start_p = 81000.0 if symbol == Underlying.SENSEX else 24800.0
        sample_bars = loader.load_or_generate_dataset(symbol=symbol, days=1, start_price=start_p)

        print("[*] Streaming live 5-minute ticks with synchronized telemetry...")
        print("------------------------------------------------------------------")

        try:
            for bar in sample_bars[:45]:
                # Simulate countdown to bar close
                for remaining_s in range(3, 0, -1):
                    daemon.render_live_telemetry(bar.timestamp, remaining_s)
                    time.sleep(0.4)  # Fast live playback

                # Candle close event
                daemon.on_candle_close(bar)
                daemon.render_live_telemetry(bar.timestamp, 0)
                time.sleep(0.3)

            print("\n\n[*] Live morning paper-trading cycle complete.")
        except KeyboardInterrupt:
            print("\n\n[*] Stopped by user.")
    else:
        print("[*] Market is OPEN. Initializing real-time exchange feed listener...")
        from data_engine.live_feed import LiveFeedFetcher
        feed_fetcher = LiveFeedFetcher(symbol)

        # Pre-load today's existing morning bars if starting mid-session
        existing_bars = feed_fetcher.fetch_today_5m_bars()
        if existing_bars:
            print(f"[*] Pre-loading {len(existing_bars)} session bars up to {existing_bars[-1].timestamp.strftime('%H:%M IST')}...")
            for bar in existing_bars:
                daemon.on_candle_close(bar)
            print("[*] Session state synchronized. Listening for upcoming 5-minute candle completions...\n")

        try:
            while True:
                now = datetime.now(IST_TZ)

                if now.time() >= dtime(15, 30):
                    print("\n[*] 15:30 IST reached. Market session closed.")
                    break

                # Next 5-minute candle close boundary
                next_minute = (now.minute // 5 + 1) * 5
                if next_minute == 60:
                    next_close = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                else:
                    next_close = now.replace(minute=next_minute, second=0, microsecond=0)

                countdown_sec = int((next_close - now).total_seconds())
                daemon.render_live_telemetry(now, countdown_sec)

                # Check for newly closed bar
                if countdown_sec <= 2 or countdown_sec % 10 == 0:
                    new_bar = feed_fetcher.get_latest_closed_bar()
                    if new_bar:
                        print(f"\n[📊 5M CANDLE CLOSED] {new_bar.timestamp.strftime('%H:%M IST')} | O: {new_bar.open:.2f} H: {new_bar.high:.2f} L: {new_bar.low:.2f} C: {new_bar.close:.2f}")
                        daemon.on_candle_close(new_bar)

                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Live market runner stopped by user.")

    # Generate end of day summary report
    print("\n[*] Compiling end-of-day daily trading report...")
    from scripts.generate_daily_report import generate_report
    report = generate_report(datetime.now(IST_TZ).date())
    print("[*] Done. Have a great day!")

if __name__ == "__main__":
    main()
