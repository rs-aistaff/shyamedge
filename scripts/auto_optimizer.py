import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

import json
from itertools import combinations
from datetime import datetime
from core.constants import Underlying, StrategyID
from data_engine.parquet_loader import ParquetDataLoader
from backtest_engine.engine import BacktestEngine

def evaluate_strategy(symbol: Underlying, sid: StrategyID, bars, capital: float = 30000.0):
    engine = BacktestEngine(
        underlying=symbol,
        initial_capital=capital,
        record_to_db=False,
        enabled_strategies=[sid]
    )
    m = engine.run(bars)
    
    # Calculate composite score
    net = m["net_pnl"]
    wr = m["win_rate_pct"]
    pf = m["profit_factor"]
    dd = max(100.0, m["max_drawdown"])
    trades = m["total_trades"]
    
    # Penalize low trade count or negative PnL
    score = (wr * pf * net) / dd if net > 0 and trades >= 3 else -abs(net)
    
    return {
        "strategy_id": sid.value,
        "trades": trades,
        "wins": m["winning_trades"],
        "losses": m["losing_trades"],
        "win_rate": wr,
        "gross_pnl": m["gross_pnl"],
        "net_pnl": net,
        "profit_factor": pf,
        "expectancy": m["expectancy"],
        "max_drawdown": m["max_drawdown"],
        "sharpe": m["sharpe_ratio"],
        "score": round(score, 2)
    }

def run_optimization():
    loader = ParquetDataLoader()
    capital = 30000.0
    
    print("\n" + "="*80)
    print("SHYAMEDGE AUTONOMOUS QUANTITATIVE STRATEGY OPTIMIZATION ENGINE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Capital: ₹{capital:,.2f}")
    print("="*80 + "\n")
    
    all_strategies = list(StrategyID)
    final_report = {}

    for symbol, start_p in [(Underlying.NIFTY50, 24500.0), (Underlying.SENSEX, 81000.0)]:
        print(f"\n[*] Optimizing for {symbol.value} across 30 days (1650 candles)...")
        bars = loader.load_or_generate_dataset(symbol=symbol, days=30, start_price=start_p)
        
        strat_results = []
        for sid in all_strategies:
            res = evaluate_strategy(symbol, sid, bars, capital)
            strat_results.append(res)
            print(f"  -> {res['strategy_id']:<18} | Trades: {res['trades']:<3} | Win%: {res['win_rate']:>5.1f}% | Net: ₹{res['net_pnl']:>9,.2f} | PF: {res['profit_factor']:>5.2f} | Score: {res['score']:>8,.1f}")

        # Sort individual strategies by score
        strat_results.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = [r["strategy_id"] for r in strat_results if r["net_pnl"] > 0 and r["win_rate"] >= 50.0]
        search_candidates = top_candidates[:5]
        
        print(f"\n[*] Top Qualifying Strategies for {symbol.value} (Win% >= 50% & Net > 0):")
        for tc in top_candidates:
            print(f"    - {tc}")

        # Now test combinations among top 5 candidates (size 1 to 3)
        print(f"\n[*] Running Portfolio Combinatorial Optimization on {symbol.value} (top {len(search_candidates)} models)...")
        best_combo = None
        best_combo_metrics = None
        best_combo_score = -999999.0

        for r_len in range(1, min(4, len(search_candidates) + 1)):
            for combo in combinations(search_candidates, r_len):
                combo_sids = [StrategyID(c) for c in combo]
                engine = BacktestEngine(
                    underlying=symbol,
                    initial_capital=capital,
                    record_to_db=False,
                    enabled_strategies=combo_sids
                )
                m = engine.run(bars)
                
                c_net = m["net_pnl"]
                c_wr = m["win_rate_pct"]
                c_pf = m["profit_factor"]
                c_dd = max(100.0, m["max_drawdown"])
                c_trades = m["total_trades"]
                
                # We target: Win Rate >= 60%, Net PnL > 0, PF >= 2.0
                if c_wr >= 60.0 and c_net > 0 and c_trades >= 5:
                    c_score = (c_wr * c_pf * c_net) / c_dd
                    if c_score > best_combo_score:
                        best_combo_score = c_score
                        best_combo = combo
                        best_combo_metrics = m

        if best_combo and best_combo_metrics:
            print(f"\n[🏆] OPTIMAL ELITE BASKET DISCOVERED FOR {symbol.value}:")
            print(f"    Strategies   : {list(best_combo)}")
            print(f"    Total Trades : {best_combo_metrics['total_trades']}")
            print(f"    Win Rate     : {best_combo_metrics['win_rate_pct']:.1f}% ({best_combo_metrics['winning_trades']}W / {best_combo_metrics['losing_trades']}L)")
            print(f"    Net Realized : ₹{best_combo_metrics['net_pnl']:+,.2f} ({best_combo_metrics['return_on_capital_pct']:+.2f}%)")
            print(f"    Profit Factor: {best_combo_metrics['profit_factor']:.2f}")
            print(f"    Expectancy   : ₹{best_combo_metrics['expectancy']:+,.2f}")
            print(f"    Max Drawdown : ₹{best_combo_metrics['max_drawdown']:,.2f}")
            print(f"    Sharpe Ratio : {best_combo_metrics['sharpe_ratio']:.2f}")
            final_report[symbol.value] = {
                "optimal_basket": list(best_combo),
                "metrics": best_combo_metrics,
                "individual_rankings": strat_results
            }
        else:
            print(f"[-] No combination met the strict >=60% criteria, fallback to top single candidate.")
            fallback = [top_candidates[0]] if top_candidates else [StrategyID.EMA_CROSSOVER.value]
            final_report[symbol.value] = {
                "optimal_basket": fallback,
                "individual_rankings": strat_results
            }

    print("\n" + "="*80)
    print("OPTIMIZATION ENGINE COMPLETE")
    print("="*80 + "\n")
    return final_report

if __name__ == "__main__":
    run_optimization()
