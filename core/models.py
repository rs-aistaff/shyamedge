from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from core.constants import (
    Underlying, OptionType, SignalDirection, StrategyID,
    MarketRegime, OrderSide, OrderType, OrderStatus, PositionStatus
)

class Bar(BaseModel):
    timestamp: datetime
    symbol: Underlying
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    timeframe: str = "5m"
    vwap: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    rsi_14: Optional[float] = None
    atr_14: Optional[float] = None
    regime: Optional[MarketRegime] = None

class Signal(BaseModel):
    signal_id: UUID = Field(default_factory=uuid4)
    run_id: Optional[UUID] = None
    timestamp: datetime
    strategy_id: StrategyID
    strategy_version: str = "v1.0"
    underlying: Underlying
    direction: SignalDirection
    signal_score: float = Field(ge=0.0, le=100.0)
    market_regime: MarketRegime
    underlying_price: float
    suggested_strike: Optional[float] = None
    suggested_expiry: Optional[date] = None
    is_accepted: bool = False
    rejection_reason: Optional[str] = None
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Order(BaseModel):
    order_id: UUID = Field(default_factory=uuid4)
    signal_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
    timestamp: datetime
    option_symbol: str
    order_side: OrderSide
    order_type: OrderType = OrderType.MARKET
    quantity: int
    requested_price: float
    executed_price: Optional[float] = None
    slippage: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    rejection_reason: Optional[str] = None

class Position(BaseModel):
    position_id: UUID = Field(default_factory=uuid4)
    run_id: Optional[UUID] = None
    strategy_id: StrategyID
    option_symbol: str
    underlying: Underlying
    option_type: OptionType
    strike: float
    expiry: date
    quantity: int
    entry_time: datetime
    entry_price: float
    current_price: float
    stop_loss: float
    target: float
    trailing_sl: Optional[float] = None
    unrealized_pnl: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Trade(BaseModel):
    trade_id: UUID = Field(default_factory=uuid4)
    run_id: Optional[UUID] = None
    strategy_id: StrategyID
    strategy_version: str = "v1.0"
    underlying: Underlying
    option_symbol: str
    expiry_date: date
    strike: float
    option_type: OptionType
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    quantity: int
    gross_pnl: float
    brokerage: float
    stt: float
    exchange_charges: float
    gst: float
    sebi_charges: float
    stamp_duty: float
    total_charges: float
    slippage: float
    net_pnl: float
    return_pct: float
    entry_reason: str
    exit_reason: str
    signal_score: float
    market_regime: MarketRegime
    holding_time_minutes: int
