class ShyamEdgeException(Exception):
    """Base exception for all ShyamEdge domain exceptions."""
    pass

class RiskBreachException(ShyamEdgeException):
    """Raised when a trade violates portfolio risk parameters."""
    pass

class InsufficientCapitalException(RiskBreachException):
    """Raised when ₹15,000 portfolio has insufficient capital for an option premium."""
    pass

class DailyLossLimitExceededException(RiskBreachException):
    """Raised when 3% (₹450) daily loss ceiling is hit."""
    pass

class KillSwitchActivatedException(RiskBreachException):
    """Raised when system kill switch is triggered."""
    pass

class PositionLimitExceededException(RiskBreachException):
    """Raised when attempting to exceed maximum concurrent open positions (1)."""
    pass

class BrokerExecutionException(ShyamEdgeException):
    """Raised during broker communication or order execution failure."""
    pass

class DataFeedException(ShyamEdgeException):
    """Raised on missing, corrupted, or stale market data."""
    pass
