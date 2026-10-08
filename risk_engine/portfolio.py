from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from core.models import Position, Trade
from core.exceptions import PositionLimitExceededException, DailyLossLimitExceededException

class VirtualPortfolio:
    """
    Unified ₹15,000 Virtual Capital Portfolio Manager.
    Maintains portfolio-level state while tracking independent per-strategy performance.
    """
    def __init__(self, initial_capital: float = 15000.0, max_daily_loss_pct: float = 0.03):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.cash = initial_capital
        self.max_daily_loss_pct = max_daily_loss_pct

        # Daily tracking
        self.current_date: Optional[date] = None
        self.daily_starting_capital = initial_capital
        self.daily_realized_pnl: float = 0.0
        self.daily_trade_count: int = 0
        self.daily_loss_limit_hit: bool = False

        # Active position (Max 1 allowed)
        self.active_position: Optional[Position] = None

        # Per-strategy analytics
        self.strategy_stats: Dict[str, Dict[str, float]] = {
            "ORB": {"trades": 0, "wins": 0, "losses": 0, "net_pnl": 0.0},
            "VWAP_EMA": {"trades": 0, "wins": 0, "losses": 0, "net_pnl": 0.0},
            "PULLBACK": {"trades": 0, "wins": 0, "losses": 0, "net_pnl": 0.0},
            "BREAKOUT_VOL": {"trades": 0, "wins": 0, "losses": 0, "net_pnl": 0.0}
        }

        # Consecutive loss counter
        self.consecutive_losses: int = 0
        self.peak_capital = initial_capital
        self.max_drawdown: float = 0.0

    def check_new_day(self, current_dt: datetime):
        today = current_dt.date()
        if self.current_date != today:
            self.current_date = today
            self.daily_starting_capital = self.current_capital
            self.daily_realized_pnl = 0.0
            self.daily_trade_count = 0
            self.daily_loss_limit_hit = False
            self.consecutive_losses = 0  # Reset intraday loss counter on fresh session

    @property
    def max_daily_loss_amount(self) -> float:
        return self.daily_starting_capital * self.max_daily_loss_pct

    def can_open_position(self, current_dt: datetime) -> Tuple[bool, str]:
        self.check_new_day(current_dt)

        if self.daily_loss_limit_hit:
            return False, "CIRCUIT_BREAKER_DAILY_LOSS_LIMIT_HIT"

        if self.active_position is not None:
            return False, "POSITION_LIMIT_EXCEEDED_ALREADY_OPEN"

        if self.daily_trade_count >= 3:
            return False, "MAX_DAILY_TRADES_LIMIT_REACHED"

        if self.consecutive_losses >= 2:
            return False, "CONSECUTIVE_LOSS_COOLDOWN"

        return True, ""

    def register_entry(self, position: Position):
        self.check_new_day(position.entry_time)
        if self.active_position is not None:
            raise PositionLimitExceededException("Only 1 concurrent open position is permitted.")

        cost = position.entry_price * position.quantity
        self.cash -= cost
        self.active_position = position
        self.daily_trade_count += 1

    def register_exit(self, trade: Trade):
        self.check_new_day(trade.exit_time)
        self.current_capital += trade.net_pnl
        self.cash = self.current_capital
        self.daily_realized_pnl += trade.net_pnl
        self.active_position = None

        # Update strategy attribution dynamically across all 15 strategies
        strat_key = trade.strategy_id.value if hasattr(trade.strategy_id, 'value') else str(trade.strategy_id)
        if strat_key not in self.strategy_stats:
            self.strategy_stats[strat_key] = {"trades": 0, "wins": 0, "losses": 0, "net_pnl": 0.0}

        stats = self.strategy_stats[strat_key]
        stats["trades"] += 1
        stats["net_pnl"] += trade.net_pnl
        if trade.net_pnl > 0:
            stats["wins"] += 1
            self.consecutive_losses = 0
        else:
            stats["losses"] += 1
            self.consecutive_losses += 1

        # Track Drawdown
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        current_dd = self.peak_capital - self.current_capital
        if current_dd > self.max_drawdown:
            self.max_drawdown = current_dd

        # Check Daily Loss Circuit Breaker
        if self.daily_realized_pnl <= -self.max_daily_loss_amount:
            self.daily_loss_limit_hit = True
