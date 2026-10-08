import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

from core.constants import Underlying, StrategyID
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine

def run_ensemble():
    loader = ParquetDataLoader()
    
    # Core Alpha Ensemble: Donchian + Breakout Vol + Pivot Reversal
    ensemble = [StrategyID.DONCHIAN, StrategyID.BREAKOUT_VOL, StrategyID.PIVOT_REVERSAL]
    
    for symbol, start_p in [(Underlying.NIFTY50, 24500.0), (Underlying.SENSEX, 81000.0)]:
        bars = loader.load_or_generate_dataset(symbol=symbol, days=30, start_price=start_p)
        engine = BacktestEngine(
            underlying=symbol,
            initial_capital=30000.0,
            record_to_db=False,
            enabled_strategies=ensemble
        )
        m = engine.run(bars)
        print(f"\n==================================================================")
        print(f"CORE ALPHA ENSEMBLE ON {symbol.value} (30 DAYS, CAPITAL ₹30,000)")
        print(f"==================================================================")
        print(f"Total Trades   : {m['total_trades']}")
        print(f"Win Rate       : {m['win_rate_pct']:.1f}% ({m['winning_trades']}W / {m['losing_trades']}L)")
        print(f"Net Realized   : ₹{m['net_pnl']:+,.2f} ({m['return_on_capital_pct']:+.2f}%)")
        print(f"Gross P&L      : ₹{m['gross_pnl']:+,.2f}")
        print(f"Statutory Taxes: ₹{m['total_charges']:,.2f}")
        print(f"Slippage Drag  : ₹{m['total_slippage']:,.2f}")
        print(f"Profit Factor  : {m['profit_factor']:.2f}")
        print(f"Expectancy     : ₹{m['expectancy']:+,.2f}")
        print(f"Max Drawdown   : ₹{m['max_drawdown']:,.2f}")
        print(f"Sharpe Ratio   : {m['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio  : {m['sortino_ratio']:.2f}")
        print("------------------------------------------------------------------")
        for strat, data in m["strategy_breakdown"].items():
            print(f"  {strat:<18}: {data['trades']} trades | {data.get('win_rate_pct', 0.0):.1f}% WR | ₹{data.get('net_pnl', 0.0):+,.2f} | PF: {data.get('profit_factor', 0.0):.2f}")

if __name__ == "__main__":
    run_ensemble()
