import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

from core.constants import Underlying, StrategyID
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine

def test_instrument(symbol: Underlying, days: int = 30, capital: float = 30000.0):
    start_price = 24500.0 if symbol == Underlying.NIFTY50 else 81000.0
    loader = ParquetDataLoader()
    bars = loader.load_or_generate_dataset(symbol=symbol, days=days, start_price=start_price)
    
    print(f"\n=========================================================================================")
    print(f"TESTING ALL 15 STRATEGIES ON {symbol.value} (30 DAYS, {len(bars)} BARS, CAPITAL ₹{capital:,.0f})")
    print(f"=========================================================================================")
    print(f"{'Strategy':<20} | {'Trades':<6} | {'Win%':<7} | {'Gross P&L':<12} | {'Net P&L':<12} | {'PF':<6} | {'Expectancy':<10}")
    print(f"-----------------------------------------------------------------------------------------")

    all_strategies = list(StrategyID)
    results = []

    for sid in all_strategies:
        engine = BacktestEngine(
            underlying=symbol,
            initial_capital=capital,
            record_to_db=False,
            enabled_strategies=[sid]
        )
        metrics = engine.run(bars)
        t = metrics["total_trades"]
        wr = metrics["win_rate_pct"]
        gross = metrics["gross_pnl"]
        net = metrics["net_pnl"]
        pf = metrics["profit_factor"]
        exp = metrics["expectancy"]

        results.append({
            "sid": sid,
            "trades": t,
            "wr": wr,
            "gross": gross,
            "net": net,
            "pf": pf,
            "exp": exp
        })

        print(f"{sid.value:<20} | {t:<6} | {wr:>6.1f}% | ₹{gross:>10,.2f} | ₹{net:>10,.2f} | {pf:>5.2f} | ₹{exp:>8.2f}")

    print(f"=========================================================================================\n")
    return results

if __name__ == "__main__":
    nifty_res = test_instrument(Underlying.NIFTY50)
    sensex_res = test_instrument(Underlying.SENSEX)
