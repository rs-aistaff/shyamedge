import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

from core.constants import Underlying, StrategyID
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine

def run_test():
    loader = ParquetDataLoader()
    basket = [StrategyID.DONCHIAN, StrategyID.BREAKOUT_VOL, StrategyID.PIVOT_REVERSAL, StrategyID.GAP_CONTINUATION]
    
    for symbol, start_p in [(Underlying.NIFTY50, 24500.0), (Underlying.SENSEX, 81000.0)]:
        bars = loader.load_or_generate_dataset(symbol=symbol, days=30, start_price=start_p)
        engine = BacktestEngine(underlying=symbol, initial_capital=30000.0, record_to_db=False, enabled_strategies=basket)
        m = engine.run(bars)
        print(f"{symbol.value:<10} | Trades: {m['total_trades']:<3} | Win%: {m['win_rate_pct']:>5.1f}% | Net: ₹{m['net_pnl']:>10,.2f} | PF: {m['profit_factor']:>5.2f} | Exp: ₹{m['expectancy']:>7.2f}")

if __name__ == "__main__":
    run_test()
