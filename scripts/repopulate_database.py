import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

import sqlite3
from core.constants import Underlying, StrategyID, LOT_SIZES
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine
from database.connection import init_db

def repopulate():
    print("==================================================================")
    print("REPOPULATING SHYAMEDGE DATABASE WITH ACCURATE LOT SIZES & EXITS")
    print(f"Official Lot Sizes: NIFTY50 = {LOT_SIZES[Underlying.NIFTY50]} | SENSEX = {LOT_SIZES[Underlying.SENSEX]}")
    print("==================================================================\n")

    init_db()

    # Clear previous trades and positions
    conn = sqlite3.connect("shyam_edge.db")
    c = conn.cursor()
    c.execute("DELETE FROM trades")
    c.execute("DELETE FROM positions")
    c.execute("DELETE FROM signals")
    c.execute("DELETE FROM orders")
    conn.commit()
    conn.close()
    print("[*] Cleared old records from database tables.")

    loader = ParquetDataLoader()
    basket = [
        StrategyID.DONCHIAN,
        StrategyID.BREAKOUT_VOL,
        StrategyID.PIVOT_REVERSAL,
        StrategyID.GAP_CONTINUATION
    ]

    total_trades = 0
    total_net = 0.0

    for symbol, start_p in [(Underlying.NIFTY50, 24500.0), (Underlying.SENSEX, 81000.0)]:
        print(f"\n[*] Processing {symbol.value} (Lot size: {LOT_SIZES[symbol]})...")
        bars = loader.load_or_generate_dataset(symbol=symbol, days=30, start_price=start_p)
        engine = BacktestEngine(
            underlying=symbol,
            initial_capital=30000.0,
            record_to_db=True,
            enabled_strategies=basket
        )
        m = engine.run(bars)
        print(f"    Trades: {m['total_trades']} | Win Rate: {m['win_rate_pct']:.1f}% | Net P&L: ₹{m['net_pnl']:+,.2f} | PF: {m['profit_factor']:.2f}")
        total_trades += m['total_trades']
        total_net += m['net_pnl']

    # Verification query
    conn = sqlite3.connect("shyam_edge.db")
    c = conn.cursor()
    c.execute("SELECT underlying, quantity, COUNT(*) FROM trades GROUP BY underlying, quantity")
    lot_counts = c.fetchall()
    c.execute("SELECT exit_reason, COUNT(*) FROM trades GROUP BY exit_reason")
    exit_counts = c.fetchall()
    c.execute("SELECT COUNT(*), SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END), SUM(gross_pnl), SUM(total_charges + slippage), SUM(net_pnl) FROM trades")
    t_tot, t_win, t_gross, t_drag, t_net = c.fetchone()
    conn.close()

    print("\n==================================================================")
    print("DATABASE REPOPULATION COMPLETE & VERIFIED")
    print(f"Total Database Trades : {t_tot}")
    print(f"Winning Trades        : {t_win} ({(t_win/t_tot*100):.1f}% Win Rate)")
    print(f"Gross P&L             : ₹{t_gross:+,.2f}")
    print(f"Total Charges & Slip  : ₹{t_drag:,.2f}")
    print(f"Net Realized P&L      : ₹{t_net:+,.2f}")
    print(f"Lot Size Verification : {lot_counts}")
    print(f"Exit Reason Breakdown : {exit_counts}")
    print("==================================================================")

if __name__ == "__main__":
    repopulate()
