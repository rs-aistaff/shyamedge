import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    Text, JSON, ForeignKey, BigInteger
)
from sqlalchemy.orm import relationship
from database.connection import Base

def generate_uuid():
    return str(uuid.uuid4())

class MarketDataDB(Base):
    __tablename__ = "market_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(32), nullable=False, index=True)
    timeframe = Column(String(8), nullable=False, default="5m")
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False, default=0)
    vwap = Column(Float, nullable=True)
    ema_20 = Column(Float, nullable=True)
    ema_50 = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)
    regime = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class OptionContractDB(Base):
    __tablename__ = "option_contracts"

    contract_id = Column(String(64), primary_key=True)
    underlying = Column(String(32), nullable=False, index=True)
    strike = Column(Float, nullable=False)
    option_type = Column(String(4), nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    lot_size = Column(Integer, nullable=False)
    tick_size = Column(Float, default=0.05)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StrategyRunDB(Base):
    __tablename__ = "strategy_runs"

    run_id = Column(String(36), primary_key=True, default=generate_uuid)
    mode = Column(String(16), nullable=False)  # BACKTEST | PAPER | LIVE
    strategy_id = Column(String(32), nullable=False)
    strategy_version = Column(String(16), nullable=False, default="v1.0")
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    parameters = Column(JSON, default=dict)
    initial_capital = Column(Float, default=15000.0)
    final_capital = Column(Float, nullable=True)
    status = Column(String(16), default="ACTIVE")

class SignalDB(Base):
    __tablename__ = "signals"

    signal_id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("strategy_runs.run_id"), nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    strategy_id = Column(String(32), nullable=False, index=True)
    underlying = Column(String(32), nullable=False)
    direction = Column(String(8), nullable=False)
    signal_score = Column(Float, nullable=False)
    market_regime = Column(String(32), nullable=False)
    underlying_price = Column(Float, nullable=False)
    suggested_strike = Column(Float, nullable=True)
    suggested_expiry = Column(Date, nullable=True)
    score_breakdown = Column(JSON, default=dict)
    is_accepted = Column(Boolean, nullable=False)
    rejection_reason = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class OrderDB(Base):
    __tablename__ = "orders"

    order_id = Column(String(36), primary_key=True, default=generate_uuid)
    signal_id = Column(String(36), ForeignKey("signals.signal_id"), nullable=True)
    run_id = Column(String(36), ForeignKey("strategy_runs.run_id"), nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    option_symbol = Column(String(64), nullable=False)
    order_side = Column(String(8), nullable=False)
    order_type = Column(String(16), default="MARKET")
    quantity = Column(Integer, nullable=False)
    requested_price = Column(Float, nullable=False)
    executed_price = Column(Float, nullable=True)
    slippage = Column(Float, default=0.0)
    status = Column(String(16), nullable=False, default="PENDING")
    rejection_reason = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PositionDB(Base):
    __tablename__ = "positions"

    position_id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("strategy_runs.run_id"), nullable=True)
    strategy_id = Column(String(32), nullable=False)
    option_symbol = Column(String(64), nullable=False)
    underlying = Column(String(32), nullable=False)
    option_type = Column(String(4), nullable=False)
    strike = Column(Float, nullable=False)
    expiry = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_time = Column(DateTime, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target = Column(Float, nullable=False)
    trailing_sl = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    status = Column(String(16), default="OPEN")

class TradeDB(Base):
    __tablename__ = "trades"

    trade_id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("strategy_runs.run_id"), nullable=True)
    strategy_id = Column(String(32), nullable=False, index=True)
    strategy_version = Column(String(16), nullable=False, default="v1.0")
    underlying = Column(String(32), nullable=False)
    option_symbol = Column(String(64), nullable=False)
    expiry_date = Column(Date, nullable=False)
    strike = Column(Float, nullable=False)
    option_type = Column(String(4), nullable=False)
    entry_time = Column(DateTime, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_time = Column(DateTime, nullable=False, index=True)
    exit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    gross_pnl = Column(Float, nullable=False)
    brokerage = Column(Float, nullable=False)
    stt = Column(Float, nullable=False)
    exchange_charges = Column(Float, nullable=False)
    gst = Column(Float, nullable=False)
    sebi_charges = Column(Float, nullable=False)
    stamp_duty = Column(Float, nullable=False)
    total_charges = Column(Float, nullable=False)
    slippage = Column(Float, nullable=False)
    net_pnl = Column(Float, nullable=False)
    return_pct = Column(Float, nullable=False)
    entry_reason = Column(String(256), nullable=False)
    exit_reason = Column(String(256), nullable=False)
    signal_score = Column(Float, nullable=False)
    market_regime = Column(String(32), nullable=False)
    holding_time_minutes = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DailyPnLDB(Base):
    __tablename__ = "daily_pnl"

    pnl_date = Column(Date, primary_key=True)
    starting_balance = Column(Float, default=15000.0)
    ending_balance = Column(Float, nullable=False)
    gross_pnl = Column(Float, default=0.0)
    total_charges = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    max_drawdown = Column(Float, default=0.0)
    daily_loss_limit_hit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RiskEventDB(Base):
    __tablename__ = "risk_events"

    event_id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_type = Column(String(64), nullable=False)
    severity = Column(String(16), nullable=False)
    message = Column(Text, nullable=False)
    context_data = Column(JSON, default=dict)

class SystemEventDB(Base):
    __tablename__ = "system_events"

    event_id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    component = Column(String(32), nullable=False)
    level = Column(String(16), nullable=False)
    message = Column(Text, nullable=False)
