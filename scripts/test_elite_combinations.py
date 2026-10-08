import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

from core.constants import Underlying, StrategyID
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine

def test_combination(symbol: Underlying, strats, label: str):
    loader = ParquetDataLoader()
    start_price = 24500.0 if symbol == Underlying.NIFTY50 else 81000.0
    bars = loader.load_or_generate_dataset(symbol=symbol, days=30, start_price=start_price)
    
    engine = BacktestEngine(
        underlying=symbol,
        initial_capital=30000.0,
        record_to_db=False,
        enabled_strategies=strats
    )
    m = engine.run(bars)
    print(f"\n==================================================================")
    print(f"{label} on {symbol.value}")
    print(f"==================================================================")
    print(f"Total Trades   : {m['total_trades']}")
    print(f"Win Rate       : {m['win_rate_pct']:.1f}% ({m['winning_trades']}W / {m['losing_trades']}L)")
    print(f"Net Realized   : ₹{m['net_pnl']:+,.2f} ({m['return_on_capital_pct']:+.2f}%)")
    print(f"Gross P&L      : ₹{m['gross_pnl']:+,.2f}")
    print(f"Charges & Slip : ₹{m['total_charges'] + m['total_slippage']:,.2f}")
    print(f"Profit Factor  : {m['profit_factor']:.2f}")
    print(f"Expectancy     : ₹{m['expectancy']:+,.2f}")
    print(f"Max Drawdown   : ₹{m['max_drawdown']:,.2f}")
    print("------------------------------------------------------------------")
    for strat, data in m["strategy_breakdown"].items():
        print(f"  {strat:<18}: {data['trades']} trades | {data.get('win_rate_pct', 0.0):.1f}% WR | ₹{data.get('net_pnl', 0.0):+,.2f}")
    return m

if __name__ == "__main__":
    # Test SENSEX elite basket: EMA_CROSSOVER, GAP_CONTINUATION, RSI_EXPANSION
    test_combination(
        Underlying.SENSEX,
        [StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION, StrategyID.RSI_EXPANSION],
        "SENSEX ELITE BASKET"
    )
    
    # Test NIFTY50 elite basket: EMA_CROSSOVER, GAP_CONTINUATION, DONCHIAN, VWAP_BOUNCE, PIVOT_REVERSAL
    test_combination(
        Underlying.NIFTY50,
        [StrategyID.EMA_CROSSOVER, StrategyID.GAP_CONTINUATION, StrategyID.DONCHIAN, StrategyID.VWAP_BOUNCE, StrategyID.PIVOT_REVERSAL],
        "NIFTY50 ELITE BASKET"
    )
