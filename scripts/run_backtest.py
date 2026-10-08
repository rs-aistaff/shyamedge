import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import argparse
from datetime import datetime
from core.constants import Underlying, StrategyID
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine
from database.repository import Repository

def main():
    parser = argparse.ArgumentParser(description="Run ShyamEdge Historical Backtest")
    parser.add_argument("--symbol", type=str, default="NIFTY50", choices=["NIFTY50", "SENSEX"])
    parser.add_argument("--days", type=int, default=30, help="Number of trading days to test")
    parser.add_argument("--capital", type=float, default=30000.0, help="Initial virtual capital")
    parser.add_argument("--record-db", action="store_true", help="Record backtest trades and signals to SQLite database")
    parser.add_argument("--clear-db", action="store_true", help="Clear existing DB records before running")
    parser.add_argument("--strategies", type=str, default="elite", choices=["elite", "all"], help="Strategy selection basket (elite = high win-rate >=60%% filtered basket; all = all 15 strategies)")
    args = parser.parse_args()

    if args.clear_db:
        print("[*] Clearing historical database records before running...")
        Repository.clear_all_data()
        print("[*] Database cleared successfully.")

    symbol = Underlying(args.symbol)
    print(f"\n==================================================================")
    print(f"SHYAMEDGE OPTIONS BUYING HISTORICAL BACKTEST ENGINE")
    print(f"Underlying: {symbol.value} | Capital: ₹{args.capital:,.2f} | Days: {args.days} | Basket: {args.strategies.upper()}")
    print(f"==================================================================\n")

    # Load / synthesize 5-minute bars
    loader = ParquetDataLoader()
    start_price = 24500.0 if symbol == Underlying.NIFTY50 else 81000.0
    print(f"[*] Loading 5-minute bars for {symbol.value}...")
    bars = loader.load_or_generate_dataset(symbol=symbol, days=args.days, start_price=start_price)
    print(f"[*] Loaded {len(bars)} 5-minute candles.")

    # Determine enabled strategies
    enabled_strats = None
    if args.strategies == "all":
        enabled_strats = list(StrategyID)

    # Initialize and execute backtest engine
    engine = BacktestEngine(
        underlying=symbol,
        initial_capital=args.capital,
        record_to_db=args.record_db,
        enabled_strategies=enabled_strats
    )
    print(f"[*] Simulating bar-by-bar execution across {args.strategies.upper()} quant strategies...")
    metrics = engine.run(bars)

    print("\n==================================================================")
    print("BACKTEST RESULTS SUMMARY")
    print("==================================================================")
    print(f"Initial Capital       : ₹{metrics['initial_capital']:,.2f}")
    print(f"Final Capital         : ₹{metrics['final_capital']:,.2f}")
    print(f"Net Realized P&L      : ₹{metrics['net_pnl']:+,.2f} ({metrics['return_on_capital_pct']:+.2f}%)")
    print(f"Gross P&L             : ₹{metrics['gross_pnl']:+,.2f}")
    print(f"Statutory Charges     : ₹{metrics['total_charges']:,.2f}")
    print(f"Slippage Drag         : ₹{metrics['total_slippage']:,.2f}")
    print(f"Total Trades          : {metrics['total_trades']}")
    print(f"Winning Trades        : {metrics['winning_trades']} ({metrics['win_rate_pct']:.1f}%)")
    print(f"Losing Trades         : {metrics['losing_trades']}")
    print(f"Profit Factor         : {metrics['profit_factor']:.2f}")
    print(f"Expectancy / Trade    : ₹{metrics['expectancy']:+,.2f}")
    print(f"Max Drawdown          : ₹{metrics['max_drawdown']:,.2f}")
    print(f"Sharpe Ratio (Ann.)   : {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio (Ann.)  : {metrics['sortino_ratio']:.2f}")
    print(f"Total Signals Emitted : {metrics['total_signals_generated']} (Accepted: {metrics['signals_accepted']}, Rejected: {metrics['signals_rejected']})")

    print("\n----------------------------------------------------------------------------------------------------------")
    print(f"{'Strategy':<18} | {'Trades':<6} | {'Win Rate':<8} | {'Gross P&L':<12} | {'Net P&L':<12} | {'PF':<6} | {'Expectancy':<10}")
    print("----------------------------------------------------------------------------------------------------------")
    for strat, data in metrics["strategy_breakdown"].items():
        print(f"{strat:<18} | {data['trades']:<6} | {data.get('win_rate_pct', 0.0):>7.1f}% | ₹{data.get('gross_pnl', 0.0):>10,.2f} | ₹{data.get('net_pnl', 0.0):>10,.2f} | {data.get('profit_factor', 0.0):>5.2f} | ₹{data.get('expectancy', 0.0):>8.2f}")
    print("==========================================================================================================\n")

if __name__ == "__main__":
    main()
