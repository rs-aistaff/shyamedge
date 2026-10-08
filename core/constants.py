from enum import Enum

class Underlying(str, Enum):
    NIFTY50 = "NIFTY50"
    SENSEX = "SENSEX"

class OptionType(str, Enum):
    CE = "CE"
    PE = "PE"

class SignalDirection(str, Enum):
    BUY_CE = "BUY_CE"
    BUY_PE = "BUY_PE"
    NO_TRADE = "NO_TRADE"

class StrategyID(str, Enum):
    ORB = "ORB"
    VWAP_EMA = "VWAP_EMA"
    PULLBACK = "PULLBACK"
    BREAKOUT_VOL = "BREAKOUT_VOL"
    CPR_BREAKOUT = "CPR_BREAKOUT"
    VOL_SQUEEZE = "VOL_SQUEEZE"
    SUPERTREND_MOM = "SUPERTREND_MOM"
    INSIDE_BAR = "INSIDE_BAR"
    RSI_EXPANSION = "RSI_EXPANSION"
    EMA_CROSSOVER = "EMA_CROSSOVER"
    DONCHIAN = "DONCHIAN"
    VWAP_BOUNCE = "VWAP_BOUNCE"
    GAP_CONTINUATION = "GAP_CONTINUATION"
    ATR_SURGE = "ATR_SURGE"
    PIVOT_REVERSAL = "PIVOT_REVERSAL"

class MarketRegime(str, Enum):
    STRONG_BULLISH = "STRONG_BULLISH"
    WEAK_BULLISH = "WEAK_BULLISH"
    STRONG_BEARISH = "STRONG_BEARISH"
    WEAK_BEARISH = "WEAK_BEARISH"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    UNCLEAR = "UNCLEAR"

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class PositionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

# Exchange lot sizes (Official NSE/BSE derivative contract specifications)
LOT_SIZES = {
    Underlying.NIFTY50: 65,  # Official NSE NIFTY 50 Option Contract Lot Size (Revised to 65)
    Underlying.SENSEX: 20    # Official BSE SENSEX Option Contract Lot Size
}

# Expiry days: 1 = Tuesday (NIFTY), 3 = Thursday (SENSEX)
EXPIRY_WEEKDAYS = {
    Underlying.NIFTY50: 1,  # Tuesday (Weekly NIFTY 50 Expiry)
    Underlying.SENSEX: 3    # Thursday (Weekly SENSEX Expiry)
}
