import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import argparse
from datetime import datetime, date
import pandas as pd
from database.connection import init_db
from database.repository import Repository
from config.settings import settings

def generate_report(target_date: date) -> str:
    init_db()
    trades = Repository.get_trades(limit=100)
    df = pd.DataFrame(trades)

    if not df.empty and "exit_time" in df.columns:
        # Filter for today
        df["exit_date"] = pd.to_datetime(df["exit_time"], format="mixed").dt.date
        day_trades = df[df["exit_date"] == target_date]
    else:
        day_trades = pd.DataFrame()

    total_trades = len(day_trades)
    winning = len(day_trades[day_trades["net_pnl"] > 0]) if total_trades > 0 else 0
    losing = len(day_trades[day_trades["net_pnl"] <= 0]) if total_trades > 0 else 0
    daily_pnl = day_trades["net_pnl"].sum() if total_trades > 0 else 0.0
    win_rate = (winning / total_trades * 100) if total_trades > 0 else 0.0

    starting_cap = settings.initial_capital
    ending_cap = starting_cap + daily_pnl

    strategies = ["ORB", "VWAP_EMA", "PULLBACK", "BREAKOUT_VOL"]
    strat_perf = {}
    for s in strategies:
        if total_trades > 0:
            s_df = day_trades[day_trades["strategy_id"] == s]
            s_pnl = s_df["net_pnl"].sum()
            s_trades = len(s_df)
            strat_perf[s] = f"Trades: {s_trades} | Net P&L: ₹{s_pnl:+,.2f}"
        else:
            strat_perf[s] = "Trades: 0 | Net P&L: ₹0.00"

    report = f"""# Daily Trading Report — {target_date.strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Starting Virtual Capital:** ₹{starting_cap:,.2f}
**Ending Virtual Capital:**   ₹{ending_cap:,.2f}
**Daily Net Realized P&L:**   ₹{daily_pnl:+,.2f}
**Cumulative P&L:**          ₹{daily_pnl:+,.2f}

### Trade Performance
- **Total Executed Trades:** {total_trades}
- **Winning Trades:**        {winning}
- **Losing Trades:**         {losing}
- **Win Rate:**              {win_rate:.1f}%

### Strategy Attribution
- **ORB-v1.0:**              {strat_perf['ORB']}
- **VWAP-EMA-v1.0:**         {strat_perf['VWAP_EMA']}
- **PULLBACK-v1.0:**         {strat_perf['PULLBACK']}
- **BREAKOUT-VOL-v1.0:**     {strat_perf['BREAKOUT_VOL']}

### Risk Governance & Limits
- **Max Daily Loss Limit:**  ₹{settings.max_daily_loss_amount:.2f} (3.0%)
- **Limit Hit:**             {'YES (TRADING HALTED)' if daily_pnl <= -settings.max_daily_loss_amount else 'NO (RISK WITHIN CEILING)'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return report

def main():
    parser = argparse.ArgumentParser(description="Generate Daily ShyamEdge Trading Report")
    parser.add_argument("--date", type=str, default=datetime.utcnow().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    target_dt = datetime.strptime(args.date, "%Y-%m-%d").date()
    report_text = generate_report(target_dt)
    print(report_text)

    # Save to file
    out_file = f"daily_report_{target_dt.strftime('%Y%m%d')}.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"[*] Report saved to {out_file}")

if __name__ == "__main__":
    main()
