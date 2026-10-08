from typing import List, Dict, Any
import numpy as np
from core.models import Trade

class PerformanceAnalytics:
    """
    Computes institutional performance, risk, and expectancy metrics
    for backtest and paper-trading runs.
    """
    @classmethod
    def calculate_metrics(cls, trades: List[Trade], initial_capital: float = 15000.0) -> Dict[str, Any]:
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate_pct": 0.0,
                "gross_pnl": 0.0,
                "total_charges": 0.0,
                "total_slippage": 0.0,
                "net_pnl": 0.0,
                "return_on_capital_pct": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "strategy_breakdown": {}
            }

        total_trades = len(trades)
        wins = [t.net_pnl for t in trades if t.net_pnl > 0]
        losses = [t.net_pnl for t in trades if t.net_pnl <= 0]

        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = round((winning_trades / total_trades) * 100, 2)

        gross_pnl = round(sum(t.gross_pnl for t in trades), 2)
        total_charges = round(sum(t.total_charges for t in trades), 2)
        total_slippage = round(sum(t.slippage for t in trades), 2)
        net_pnl = round(sum(t.net_pnl for t in trades), 2)
        return_on_capital = round((net_pnl / initial_capital) * 100, 2)

        total_gain = sum(wins)
        total_loss = abs(sum(losses))
        profit_factor = round(total_gain / total_loss, 2) if total_loss > 0 else (99.0 if total_gain > 0 else 0.0)

        avg_win = round(np.mean(wins), 2) if wins else 0.0
        avg_loss = round(abs(np.mean(losses)), 2) if losses else 0.0

        # Expectancy = (Win% * AvgWin) - (Loss% * AvgLoss)
        win_prob = winning_trades / total_trades
        loss_prob = losing_trades / total_trades
        expectancy = round((win_prob * avg_win) - (loss_prob * avg_loss), 2)

        # Drawdown calculation
        equity = initial_capital
        peak = initial_capital
        max_dd = 0.0
        pnl_returns = []

        for t in trades:
            equity += t.net_pnl
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
            pnl_returns.append(t.net_pnl / initial_capital)

        # Sharpe and Sortino ratios
        if len(pnl_returns) > 1 and np.std(pnl_returns) > 0:
            mean_ret = np.mean(pnl_returns)
            std_ret = np.std(pnl_returns)
            sharpe = round(float((mean_ret / std_ret) * np.sqrt(252)), 2)
            downside_returns = [r for r in pnl_returns if r < 0]
            downside_std = np.std(downside_returns) if downside_returns else 1e-4
            sortino = round(float((mean_ret / downside_std) * np.sqrt(252)), 2)
        else:
            sharpe = 0.0
            sortino = 0.0

        # Per-strategy comprehensive attribution
        strategy_breakdown: Dict[str, Dict[str, Any]] = {}
        for t in trades:
            strat = t.strategy_id.value if hasattr(t.strategy_id, 'value') else str(t.strategy_id)
            if strat not in strategy_breakdown:
                strategy_breakdown[strat] = {
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "gross_pnl": 0.0,
                    "total_charges": 0.0,
                    "slippage": 0.0,
                    "net_pnl": 0.0,
                    "win_pnl_sum": 0.0,
                    "loss_pnl_sum": 0.0,
                }
            s = strategy_breakdown[strat]
            s["trades"] += 1
            s["gross_pnl"] = round(s["gross_pnl"] + t.gross_pnl, 2)
            s["total_charges"] = round(s["total_charges"] + t.total_charges, 2)
            s["slippage"] = round(s["slippage"] + t.slippage, 2)
            s["net_pnl"] = round(s["net_pnl"] + t.net_pnl, 2)
            if t.net_pnl > 0:
                s["wins"] += 1
                s["win_pnl_sum"] += t.net_pnl
            else:
                s["losses"] += 1
                s["loss_pnl_sum"] += abs(t.net_pnl)

        for strat, s in strategy_breakdown.items():
            tr = s["trades"]
            w = s["wins"]
            l = s["losses"]
            s["win_rate_pct"] = round((w / tr) * 100, 2) if tr > 0 else 0.0
            tot_gain = s["win_pnl_sum"]
            tot_loss = s["loss_pnl_sum"]
            s["profit_factor"] = round(tot_gain / tot_loss, 2) if tot_loss > 0 else (99.0 if tot_gain > 0 else 0.0)
            avg_w = (tot_gain / w) if w > 0 else 0.0
            avg_l = (tot_loss / l) if l > 0 else 0.0
            p_w = w / tr if tr > 0 else 0.0
            p_l = l / tr if tr > 0 else 0.0
            s["expectancy"] = round((p_w * avg_w) - (p_l * avg_l), 2)
            # Remove scratch accumulators
            del s["win_pnl_sum"]
            del s["loss_pnl_sum"]

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate_pct": win_rate,
            "gross_pnl": gross_pnl,
            "total_charges": total_charges,
            "total_slippage": total_slippage,
            "net_pnl": net_pnl,
            "return_on_capital_pct": return_on_capital,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "max_drawdown": round(max_dd, 2),
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "strategy_breakdown": strategy_breakdown
        }
