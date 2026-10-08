from datetime import datetime, date, timedelta, time
from typing import Optional, Tuple
from core.constants import Underlying, OptionType, EXPIRY_WEEKDAYS, LOT_SIZES

class OptionStrikeSelector:
    """
    Computes ATM, ITM, and OTM option strikes and expiry dates
    based on current underlying price and market conventions.
    """
    STRIKE_STEPS = {
        Underlying.NIFTY50: 50.0,
        Underlying.SENSEX: 100.0
    }

    @classmethod
    def get_nearest_expiry(cls, underlying: Underlying, current_dt: datetime) -> date:
        """
        Determines the nearest liquid weekly expiry.
        If today is expiry day and time is after 13:00 IST, rolls to the next week.
        """
        target_weekday = EXPIRY_WEEKDAYS[underlying]
        current_date = current_dt.date()
        days_ahead = (target_weekday - current_date.weekday()) % 7

        # If today is expiry day but late in the session (after 13:00 IST), rollover to next week
        if days_ahead == 0 and current_dt.time() >= time(13, 0):
            days_ahead = 7

        expiry_date = current_date + timedelta(days=days_ahead)
        return expiry_date

    @classmethod
    def calculate_atm_strike(cls, underlying: Underlying, spot_price: float) -> float:
        """Rounds spot price to the nearest ATM strike."""
        step = cls.STRIKE_STEPS[underlying]
        return round(spot_price / step) * step

    @classmethod
    def select_strike(
        cls,
        underlying: Underlying,
        spot_price: float,
        option_type: OptionType,
        prefer_itm: bool = False
    ) -> float:
        """
        Selects ATM or 1-strike ITM for options buying to ensure healthy Delta (0.50 - 0.58).
        """
        atm = cls.calculate_atm_strike(underlying, spot_price)
        step = cls.STRIKE_STEPS[underlying]

        if not prefer_itm:
            return atm

        # 1-Strike ITM
        if option_type == OptionType.CE:
            return atm - step  # Lower strike is ITM for Call
        else:
            return atm + step  # Higher strike is ITM for Put

    @classmethod
    def select_strike_for_risk_budget(
        cls,
        underlying: Underlying,
        spot_price: float,
        option_type: OptionType,
        expiry: date,
        current_dt: datetime,
        max_risk_amount: float,
        stop_loss_pct: float = 0.15,
        pricing_engine_cls = None
    ) -> Tuple[float, float]:
        """
        Adaptively chooses the best strike (starting ATM, then 1-strike OTM if needed)
        so that (Premium * StopLoss% * LotSize) fits inside the ₹15k portfolio risk budget.
        Returns: (strike, estimated_premium)
        """
        step = cls.STRIKE_STEPS[underlying]
        lot_size = LOT_SIZES[underlying]
        atm_strike = cls.calculate_atm_strike(underlying, spot_price)

        # Candidates: Target ATM first, then 1-strike ITM (Delta ~ 0.55-0.60), then 1-strike OTM
        if option_type == OptionType.CE:
            candidate_strikes = [atm_strike, atm_strike - step, atm_strike + step]
        else:
            candidate_strikes = [atm_strike, atm_strike + step, atm_strike - step]

        from data_engine.option_chain import OptionPricingEngine
        engine = pricing_engine_cls or OptionPricingEngine

        best_strike = candidate_strikes[0]
        best_premium = 50.0

        for strike in candidate_strikes:
            prem = engine.estimate_premium(
                spot=spot_price,
                strike=strike,
                option_type=option_type,
                expiry=expiry,
                current_dt=current_dt
            )
            planned_risk = prem * stop_loss_pct * lot_size
            if planned_risk <= max_risk_amount * 1.35:  # Fits risk budget with 35% tolerance
                return strike, prem
            best_strike = strike
            best_premium = prem

        return best_strike, best_premium

    @classmethod
    def generate_option_symbol(
        cls,
        underlying: Underlying,
        expiry: date,
        strike: float,
        option_type: OptionType
    ) -> str:
        """
        Generates standard trading symbol, e.g., NIFTY26OCT25000CE.
        """
        year_str = expiry.strftime("%y")
        month_str = expiry.strftime("%b").upper()
        strike_str = f"{int(strike)}"
        opt_str = option_type.value
        return f"{underlying.value}{year_str}{month_str}{strike_str}{opt_str}"
