import math
from datetime import datetime, date, time
from typing import Dict, Any, Optional
from core.constants import Underlying, OptionType

class OptionPricingEngine:
    """
    Simulates / calculates option premium pricing, intrinsic value,
    and Delta when backtesting with underlying historical data.
    """
    @classmethod
    def estimate_premium(
        cls,
        spot: float,
        strike: float,
        option_type: OptionType,
        expiry: date,
        current_dt: datetime,
        iv: float = 0.15
    ) -> float:
        """
        Estimates option premium using Black-Scholes approximation
        calibrated for Indian index options intraday dynamics.
        """
        # Time to expiration in trading days / 365
        days_remaining = max(0.01, (expiry - current_dt.date()).days)
        # Account for intraday time elapsed (session fraction)
        intraday_fraction = 1.0
        if current_dt.time() >= time(9, 15):
            mins_elapsed = (current_dt.hour - 9) * 60 + (current_dt.minute - 15)
            session_fraction = max(0.0, min(1.0, mins_elapsed / 375.0))
            days_remaining = max(0.001, days_remaining - session_fraction)

        t = days_remaining / 365.0

        # Intrinsic value
        if option_type == OptionType.CE:
            intrinsic = max(0.0, spot - strike)
        else:
            intrinsic = max(0.0, strike - spot)

        # Standard ATM time value approximation: 0.4 * S * sigma * sqrt(T)
        time_value = 0.4 * spot * iv * math.sqrt(t)

        # Dampen time value for ITM/OTM distance
        moneyness_dist = abs(spot - strike) / (spot * iv * math.sqrt(t) + 1e-5)
        dampened_tv = time_value * math.exp(-0.5 * moneyness_dist)

        premium = round(max(0.50, intrinsic + dampened_tv), 2)
        return premium
