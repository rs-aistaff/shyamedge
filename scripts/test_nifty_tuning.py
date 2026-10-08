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
    bars = loader.load_or_generate_dataset(symbol=Underlying.NIFTY50, days=30, start_price=24500.0)
    
    combos = [
        ("DONCHIAN + EMA_CROSS + GAP_CONT", [StrategyID.DONCHIAN, StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION]),
        ("DONCHIAN + EMA_CROSS + GAP_CONT + VWAP_BOUNCE", [StrategyID.DONCHIAN, StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION, StrategyID.VWAP_BOUNCE]),
        ("DONCHIAN alone", [StrategyID.DONCHIAN]),
        ("ALL 5 TOP (DONCHIAN+EMA+GAP+VWAP_BNC+PIVOT)", [StrategyID.DONCHIAN, StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION, StrategyID.VWAP_BOUNCE, StrategyID.PIVOT_REVERSAL]),
    ]
    
    for label, strats in combos:
        engine = BacktestEngine(underlying=Underlying.NIFTY50, initial_capital=30000.0, enabled_strategies=strats)
        m = engine.run(bars)
        print(f"{label:<45} | Trades: {m['total_trades']:<3} | Win%: {m['win_rate_pct']:>5.1f}% | Net P&L: ₹{m['net_pnl']:>10,.2f} | PF: {m['profit_factor']:>5.2f} | Exp: ₹{m['expectancy']:>7.2f}")

if __name__ == "__main__":
    run_test()
