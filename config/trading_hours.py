from datetime import datetime, time, date
import zoneinfo

IST_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")

class MarketSessionManager:
    """
    Manages Indian market trading sessions, intraday cutoff times,
    and operational time windows.
    """
    MARKET_OPEN = time(9, 15)
    ORB_COMPLETE = time(9, 30)
    ACTIVE_ENTRY_CUTOFF = time(14, 30)
    SQUARE_OFF_TIME = time(15, 15)
    MARKET_CLOSE = time(15, 30)

    @classmethod
    def current_ist_datetime(cls) -> datetime:
        return datetime.now(IST_TZ)

    @classmethod
    def is_market_open(cls, dt: datetime | None = None) -> bool:
        if dt is None:
            dt = cls.current_ist_datetime()
        # Monday = 0, Friday = 4, Saturday = 5, Sunday = 6
        if dt.weekday() >= 5:
            return False
        current_time = dt.time()
        return cls.MARKET_OPEN <= current_time <= cls.MARKET_CLOSE

    @classmethod
    def can_open_new_position(cls, dt: datetime | None = None) -> bool:
        if dt is None:
            dt = cls.current_ist_datetime()
        if not cls.is_market_open(dt):
            return False
        current_time = dt.time()
        # Signals only acted upon after 09:30 (ORB establishment) and before 14:30
        return cls.ORB_COMPLETE <= current_time <= cls.ACTIVE_ENTRY_CUTOFF

    @classmethod
    def is_mandatory_square_off_time(cls, dt: datetime | None = None) -> bool:
        if dt is None:
            dt = cls.current_ist_datetime()
        return dt.time() >= cls.SQUARE_OFF_TIME
