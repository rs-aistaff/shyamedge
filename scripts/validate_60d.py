import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

from core.constants import Underlying, StrategyID
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine

def run_60d_validation():
    loader = ParquetDataLoader()
    print("\n" + "="*80)
    print("60-DAY MULTI-CYCLE VALIDATION TEST (3,300 CANDLES PER INDEX)")
    print("="*80)
    
    # 1. NIFTY 50 60-Day Test
    nifty_bars = loader.load_or_generate_dataset(symbol=Underlying.NIFTY50, days=60, start_price=24500.0)
    print(f"\n[*] Running 60-day test on NIFTY50 ({len(nifty_bars)} bars)...")
    nifty_engine = BacktestEngine(
        underlying=Underlying.NIFTY50,
        initial_capital=30000.0,
        record_to_db=False,
        enabled_strategies=[
            StrategyID.DONCHIAN,
            StrategyID.EMA_CROSSOVER,
            StrategyID.GAP_CONTINUATION,
            StrategyID.VWAP_BOUNCE
        ]
    )
    n_res = nifty_engine.run(nifty_bars)
    print(f"NIFTY50 (60 Days):")
    print(f"  Trades      : {n_res['total_trades']}")
    print(f"  Win Rate    : {n_res['win_rate_pct']:.1f}% ({n_res['winning_trades']}W / {n_res['losing_trades']}L)")
    print(f"  Net Realized: ₹{n_res['net_pnl']:+,.2f} ({n_res['return_on_capital_pct']:+.2f}%)")
    print(f"  Profit Factor: {n_res['profit_factor']:.2f}")
    print(f"  Expectancy  : ₹{n_res['expectancy']:+,.2f}")
    print(f"  Max Drawdown: ₹{n_res['max_drawdown']:,.2f}")

    # 2. SENSEX 60-Day Test
    sensex_bars = loader.load_or_generate_dataset(symbol=Underlying.SENSEX, days=60, start_price=81000.0)
    print(f"\n[*] Running 60-day test on SENSEX ({len(sensex_bars)} bars)...")
    sensex_engine = BacktestEngine(
        underlying=Underlying.SENSEX,
        initial_capital=30000.0,
        record_to_db=False,
        enabled_strategies=[
            StrategyID.EMA_CROSSOVER,
            StrategyID.GAP_CONTINUATION
        ]
    )
    s_res = sensex_engine.run(sensex_bars)
    print(f"SENSEX (60 Days):")
    print(f"  Trades      : {s_res['total_trades']}")
    print(f"  Win Rate    : {s_res['win_rate_pct']:.1f}% ({s_res['winning_trades']}W / {s_res['losing_trades']}L)")
    print(f"  Net Realized: ₹{s_res['net_pnl']:+,.2f} ({s_res['return_on_capital_pct']:+.2f}%)")
    print(f"  Profit Factor: {s_res['profit_factor']:.2f}")
    print(f"  Expectancy  : ₹{s_res['expectancy']:+,.2f}")
    print(f"  Max Drawdown: ₹{s_res['max_drawdown']:,.2f}")

    print("\n" + "="*80)
    print("60-DAY MULTI-CYCLE VALIDATION COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_60d_validation()
