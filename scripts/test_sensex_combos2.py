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
    bars = loader.load_or_generate_dataset(symbol=Underlying.SENSEX, days=30, start_price=81000.0)
    
    combos = [
        ("EMA_CROSS + GAP_CONT", [StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION]),
        ("EMA_CROSS + GAP_CONT + DONCHIAN", [StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION, StrategyID.DONCHIAN]),
        ("EMA_CROSS + GAP_CONT + VWAP_BOUNCE", [StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION, StrategyID.VWAP_BOUNCE]),
        ("EMA_CROSS + GAP_CONT + PIVOT_REVERSAL", [StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION, StrategyID.PIVOT_REVERSAL]),
        ("EMA_CROSS + GAP_CONT + VOL_SQUEEZE", [StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION, StrategyID.VOL_SQUEEZE]),
    ]
    
    for label, strats in combos:
        engine = BacktestEngine(underlying=Underlying.SENSEX, initial_capital=30000.0, enabled_strategies=strats)
        m = engine.run(bars)
        print(f"{label:<45} | Trades: {m['total_trades']:<3} | Win%: {m['win_rate_pct']:>5.1f}% | Net P&L: ₹{m['net_pnl']:>10,.2f} | PF: {m['profit_factor']:>5.2f} | Exp: ₹{m['expectancy']:>7.2f}")

if __name__ == "__main__":
    run_test()
