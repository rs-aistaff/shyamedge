from database.repository import Repository

class KillSwitchManager:
    """
    Emergency circuit breaker to halt all trading operations
    and reject new paper orders.
    """
    _is_active: bool = False

    @classmethod
    def is_active(cls) -> bool:
        return cls._is_active

    @classmethod
    def activate(cls, reason: str = "Manual activation"):
        cls._is_active = True
        Repository.record_risk_event(
            event_type="KILL_SWITCH_ACTIVATED",
            severity="CRITICAL",
            message=f"Kill Switch Activated: {reason}"
        )

    @classmethod
    def deactivate(cls):
        cls._is_active = False
        Repository.record_risk_event(
            event_type="KILL_SWITCH_DEACTIVATED",
            severity="INFO",
            message="Kill Switch Deactivated: Resuming normal operational status"
        )
