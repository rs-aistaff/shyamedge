from datetime import datetime
from typing import Tuple, Optional
from core.models import Signal, Position
from risk_engine.portfolio import VirtualPortfolio
from database.repository import Repository

class RiskLimitsValidator:
    """
    Evaluates candidate trades against portfolio risk constraints.
    Enforces circuit breakers and rejects non-compliant setups.
    """
    def __init__(self, portfolio: VirtualPortfolio, kill_switch_active: bool = False):
        self.portfolio = portfolio
        self.kill_switch_active = kill_switch_active

    def can_execute_trade(self, signal: Signal, current_dt: datetime) -> Tuple[bool, str]:
        # 1. Global Kill Switch
        if self.kill_switch_active:
            Repository.record_risk_event(
                event_type="KILL_SWITCH_ACTIVE",
                severity="CRITICAL",
                message="Trade rejected: Global system kill switch is active."
            )
            return False, "KILL_SWITCH_ACTIVE"

        # 2. Daily Loss Limit & Concurrency
        can_open, reason = self.portfolio.can_open_position(current_dt)
        if not can_open:
            severity = "CRITICAL" if "DAILY_LOSS" in reason else "WARNING"
            Repository.record_risk_event(
                event_type="RISK_LIMIT_REJECT",
                severity=severity,
                message=f"Signal {signal.signal_id} rejected by risk engine: {reason}",
                context={"strategy": signal.strategy_id.value, "reason": reason}
            )
            return False, reason

        return True, ""
