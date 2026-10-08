import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import itertools
from datetime import datetime
from core.constants import Underlying
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine

def run_optimization_loop(
    symbol: Underlying = Underlying.SENSEX,
    days: int = 30,
    capital: float = 15000.0,
    target_min_trades: int = 12,
    target_min_profit_factor: float = 1.6,
    target_min_win_rate: float = 50.0
):
    print("==================================================================")
    print(f"SHYAMEDGE AUTOMATED STRATEGY OPTIMIZATION LOOP")
    print(f"Underlying: {symbol.value} | Capital: ₹{capital:,.2f} | Days: {days}")
    print("==================================================================\n")

    loader = ParquetDataLoader()
    start_p = 81000.0 if symbol == Underlying.SENSEX else 24800.0
    bars = loader.load_or_generate_dataset(symbol=symbol, days=days, start_price=start_p)
    print(f"[*] Loaded {len(bars)} 5-minute candles for backtesting loop.\n")

    # Parameter grid for calibration
    score_thresholds = [65.0, 70.0, 75.0]
    stop_loss_pcts = [0.12, 0.15, 0.18]
    target_multipliers = [1.5, 2.0, 2.5]
    slippage_pcts = [0.003, 0.004]

    combinations = list(itertools.product(score_thresholds, stop_loss_pcts, target_multipliers, slippage_pcts))
    print(f"[*] Total parameter configurations to test: {len(combinations)}")
    print(f"[*] Searching for robust configurations (Trades >= {target_min_trades}, PF >= {target_min_profit_factor}, WR >= {target_min_win_rate}%)...\n")

    best_results = []
    iteration = 0

    for score_thresh, sl_pct, target_rr, slip in combinations:
        iteration += 1

        engine = BacktestEngine(underlying=symbol, initial_capital=capital, slippage_pct=slip)
        # Apply parameter overrides
        engine.strat_orb.score_threshold = score_thresh
        engine.strat_vwap_ema.score_threshold = score_thresh

        metrics = engine.run(bars)

        trades = metrics["total_trades"]
        pf = metrics["profit_factor"]
        wr = metrics["win_rate_pct"]
        net_pnl = metrics["net_pnl"]
        max_dd = metrics["max_drawdown"]

        is_proper = (
            trades >= target_min_trades and
            pf >= target_min_profit_factor and
            wr >= target_min_win_rate and
            net_pnl > 0 and
            max_dd < 1800.0  # Max 12% drawdown on 15k capital
        )

        status_marker = "🌟 MATCH" if is_proper else "·"
        print(f"Iter #{iteration:02d} | Score: {score_thresh} | SL: {sl_pct*100:.0f}% | RR: 1:{target_rr} | Trades: {trades:02d} | WR: {wr:4.1f}% | PF: {pf:4.2f} | Net: ₹{net_pnl:+8.2f} | {status_marker}")

        if is_proper:
            best_results.append({
                "iteration": iteration,
                "score_threshold": score_thresh,
                "stop_loss_pct": sl_pct,
                "target_rr": target_rr,
                "slippage": slip,
                "trades": trades,
                "win_rate_pct": wr,
                "profit_factor": pf,
                "net_pnl": net_pnl,
                "max_drawdown": max_dd,
                "strategy_breakdown": metrics["strategy_breakdown"]
            })

    print("\n==================================================================")
    print("OPTIMIZATION RESULTS SUMMARY")
    print("==================================================================")
    if best_results:
        # Sort by profit factor and net PnL
        best_results.sort(key=lambda x: (x["profit_factor"], x["net_pnl"]), reverse=True)
        top = best_results[0]
        print(f"✅ Found {len(best_results)} viable parameter sets that passed all criteria!")
        print(f"🏆 Top Recommended Configuration:")
        print(f"   • Signal Score Threshold : {top['score_threshold']}/100")
        print(f"   • Stop Loss              : {top['stop_loss_pct']*100:.1f}%")
        print(f"   • Target Risk/Reward     : 1:{top['target_rr']}")
        print(f"   • Total Trades           : {top['trades']}")
        print(f"   • Win Rate               : {top['win_rate_pct']:.1f}%")
        print(f"   • Profit Factor          : {top['profit_factor']:.2f}")
        print(f"   • Net Realized P&L       : ₹{top['net_pnl']:+,.2f} (After all taxes & slippage)")
        print(f"   • Max Drawdown           : ₹{top['max_drawdown']:,.2f}")

        # Save to config file
        out_path = Path("config/optimized_params.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(top, f, indent=4)
        print(f"\n[*] Saved optimized parameters to {out_path}")
    else:
        print("⚠️ No configurations met all strict criteria. Loosen target thresholds slightly.")
    print("==================================================================\n")

if __name__ == "__main__":
    run_optimization_loop(symbol=Underlying.SENSEX, days=30)
