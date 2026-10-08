import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.constants import Underlying
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine

def run():
    loader = ParquetDataLoader()
    
    # NIFTY test
    nifty_bars = loader.load_or_generate_dataset(symbol=Underlying.NIFTY50, days=30, start_price=24500.0)
    engine_nifty = BacktestEngine(underlying=Underlying.NIFTY50, initial_capital=30000.0)
    m_n = engine_nifty.run(nifty_bars)
    
    print("\n--- NIFTY RESULTS ---")
    print(f"Total Trades: {m_n['total_trades']}")
    print(f"Win Rate: {m_n['win_rate_pct']}% ({m_n['winning_trades']}W / {m_n['losing_trades']}L)")
    print(f"Net P&L: ₹{m_n['net_pnl']:+,.2f}")
    print(f"Profit Factor: {m_n['profit_factor']}")
    print(f"Expectancy: ₹{m_n['expectancy']:+,.2f}")
    for s, d in m_n['strategy_breakdown'].items():
        print(f"  {s:<18}: {d['trades']} tr, {d.get('win_rate_pct',0)}% WR, Net: ₹{d['net_pnl']:+,.2f}")

    # SENSEX test
    sensex_bars = loader.load_or_generate_dataset(symbol=Underlying.SENSEX, days=30, start_price=81000.0)
    engine_sensex = BacktestEngine(underlying=Underlying.SENSEX, initial_capital=30000.0)
    m_s = engine_sensex.run(sensex_bars)
    
    print("\n--- SENSEX RESULTS ---")
    print(f"Total Trades: {m_s['total_trades']}")
    print(f"Win Rate: {m_s['win_rate_pct']}% ({m_s['winning_trades']}W / {m_s['losing_trades']}L)")
    print(f"Net P&L: ₹{m_s['net_pnl']:+,.2f}")
    print(f"Profit Factor: {m_s['profit_factor']}")
    print(f"Expectancy: ₹{m_s['expectancy']:+,.2f}")
    for s, d in m_s['strategy_breakdown'].items():
        print(f"  {s:<18}: {d['trades']} tr, {d.get('win_rate_pct',0)}% WR, Net: ₹{d['net_pnl']:+,.2f}")

if __name__ == "__main__":
    run()
