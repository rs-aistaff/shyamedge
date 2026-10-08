from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import (
    SignalDB, OrderDB, PositionDB, TradeDB,
    DailyPnLDB, RiskEventDB, SystemEventDB, StrategyRunDB
)
from config.cost_model import CostCalculator
from core.models import Signal, Order, Position, Trade

class Repository:
    """Encapsulates data persistence and querying operations."""

    @staticmethod
    def log_system_event(component: str, level: str, message: str, db: Optional[Session] = None):
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            event = SystemEventDB(
                component=component,
                level=level,
                message=message,
                timestamp=datetime.utcnow()
            )
            db.add(event)
            db.commit()
        finally:
            if own_session:
                db.close()

    @staticmethod
    def record_signal(signal: Signal, db: Optional[Session] = None) -> str:
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            sig_id = str(signal.signal_id)
            existing = db.query(SignalDB).filter(SignalDB.signal_id == sig_id).first()
            if existing:
                existing.is_accepted = signal.is_accepted
                existing.rejection_reason = signal.rejection_reason
                existing.signal_score = signal.signal_score
                db.commit()
                return sig_id

            db_signal = SignalDB(
                signal_id=sig_id,
                run_id=str(signal.run_id) if signal.run_id else None,
                timestamp=signal.timestamp,
                strategy_id=signal.strategy_id.value if hasattr(signal.strategy_id, 'value') else str(signal.strategy_id),
                underlying=signal.underlying.value if hasattr(signal.underlying, 'value') else str(signal.underlying),
                direction=signal.direction.value if hasattr(signal.direction, 'value') else str(signal.direction),
                signal_score=signal.signal_score,
                market_regime=signal.market_regime.value if hasattr(signal.market_regime, 'value') else str(signal.market_regime),
                underlying_price=signal.underlying_price,
                suggested_strike=signal.suggested_strike,
                suggested_expiry=signal.suggested_expiry,
                score_breakdown=signal.score_breakdown,
                is_accepted=signal.is_accepted,
                rejection_reason=signal.rejection_reason
            )
            db.add(db_signal)
            db.commit()
            return sig_id
        finally:
            if own_session:
                db.close()

    @staticmethod
    def record_trade(trade: Trade, db: Optional[Session] = None) -> str:
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            t_id = str(trade.trade_id)
            existing = db.query(TradeDB).filter(TradeDB.trade_id == t_id).first()
            if existing:
                return t_id

            strat_val = trade.strategy_id.value if hasattr(trade.strategy_id, 'value') else str(trade.strategy_id)
            und_val = trade.underlying.value if hasattr(trade.underlying, 'value') else str(trade.underlying)
            opt_val = trade.option_type.value if hasattr(trade.option_type, 'value') else str(trade.option_type)
            reg_val = trade.market_regime.value if hasattr(trade.market_regime, 'value') else str(trade.market_regime)

            db_trade = TradeDB(
                trade_id=t_id,
                run_id=str(trade.run_id) if trade.run_id else None,
                strategy_id=strat_val,
                strategy_version=trade.strategy_version,
                underlying=und_val,
                option_symbol=trade.option_symbol,
                expiry_date=trade.expiry_date,
                strike=trade.strike,
                option_type=opt_val,
                entry_time=trade.entry_time,
                entry_price=trade.entry_price,
                exit_time=trade.exit_time,
                exit_price=trade.exit_price,
                quantity=trade.quantity,
                gross_pnl=trade.gross_pnl,
                brokerage=trade.brokerage,
                stt=trade.stt,
                exchange_charges=trade.exchange_charges,
                gst=trade.gst,
                sebi_charges=trade.sebi_charges,
                stamp_duty=trade.stamp_duty,
                total_charges=trade.total_charges,
                slippage=trade.slippage,
                net_pnl=trade.net_pnl,
                return_pct=trade.return_pct,
                entry_reason=trade.entry_reason,
                exit_reason=trade.exit_reason,
                signal_score=trade.signal_score,
                market_regime=reg_val,
                holding_time_minutes=trade.holding_time_minutes
            )
            db.add(db_trade)
            db.commit()
            return t_id
        finally:
            if own_session:
                db.close()

    @staticmethod
    def record_risk_event(event_type: str, severity: str, message: str, context: Optional[Dict[str, Any]] = None, db: Optional[Session] = None):
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            event = RiskEventDB(
                event_type=event_type,
                severity=severity,
                message=message,
                context_data=context or {}
            )
            db.add(event)
            db.commit()
        finally:
            if own_session:
                db.close()

    @staticmethod
    def get_trades(limit: int = 100, strategy_id: Optional[str] = None, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            query = db.query(TradeDB)
            if strategy_id:
                query = query.filter(TradeDB.strategy_id == strategy_id)
            records = query.order_by(TradeDB.exit_time.desc()).limit(limit).all()
            return [
                {
                    "trade_id": r.trade_id,
                    "strategy_id": r.strategy_id,
                    "underlying": r.underlying,
                    "option_symbol": r.option_symbol,
                    "expiry_date": str(r.expiry_date),
                    "strike": r.strike,
                    "option_type": r.option_type,
                    "entry_time": r.entry_time.isoformat(),
                    "entry_price": r.entry_price,
                    "exit_time": r.exit_time.isoformat(),
                    "exit_price": r.exit_price,
                    "quantity": r.quantity,
                    "gross_pnl": r.gross_pnl,
                    "total_charges": r.total_charges,
                    "slippage": r.slippage,
                    "net_pnl": r.net_pnl,
                    "return_pct": r.return_pct,
                    "entry_reason": r.entry_reason,
                    "exit_reason": r.exit_reason,
                    "signal_score": r.signal_score,
                    "market_regime": r.market_regime,
                    "holding_time_minutes": r.holding_time_minutes
                }
                for r in records
            ]
        finally:
            if own_session:
                db.close()

    @staticmethod
    def save_or_update_position(pos: Position, db: Optional[Session] = None):
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            pos_id = str(pos.position_id)
            existing = db.query(PositionDB).filter(PositionDB.position_id == pos_id).first()
            if existing:
                existing.current_price = pos.current_price
                existing.unrealized_pnl = round((pos.current_price - pos.entry_price) * pos.quantity, 2)
                existing.trailing_sl = pos.trailing_sl
                existing.status = pos.status.value
            else:
                new_pos = PositionDB(
                    position_id=pos_id,
                    run_id=str(pos.run_id) if pos.run_id else None,
                    strategy_id=pos.strategy_id.value,
                    option_symbol=pos.option_symbol,
                    underlying=pos.underlying.value,
                    option_type=pos.option_type.value,
                    strike=pos.strike,
                    expiry=pos.expiry,
                    quantity=pos.quantity,
                    entry_time=pos.entry_time,
                    entry_price=pos.entry_price,
                    current_price=pos.current_price,
                    stop_loss=pos.stop_loss,
                    target=pos.target,
                    trailing_sl=pos.trailing_sl,
                    unrealized_pnl=round((pos.current_price - pos.entry_price) * pos.quantity, 2),
                    status=pos.status.value
                )
                db.add(new_pos)
            db.commit()
        finally:
            if own_session:
                db.close()

    @staticmethod
    def get_open_position(db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            row = db.query(PositionDB).filter(PositionDB.status == "OPEN").first()
            if not row:
                return None
            return {
                "position_id": row.position_id,
                "strategy_id": row.strategy_id,
                "option_symbol": row.option_symbol,
                "underlying": row.underlying,
                "option_type": row.option_type,
                "strike": row.strike,
                "expiry": str(row.expiry),
                "quantity": row.quantity,
                "entry_time": row.entry_time.isoformat(),
                "entry_price": row.entry_price,
                "current_price": row.current_price,
                "stop_loss": row.stop_loss,
                "target": row.target,
                "trailing_sl": row.trailing_sl,
                "unrealized_pnl": row.unrealized_pnl,
                "status": row.status
            }
        finally:
            if own_session:
                db.close()

    @staticmethod
    def close_position(position_id: str, db: Optional[Session] = None):
        """Marks a position as CLOSED and clears unrealized P&L in PositionDB."""
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            pos = db.query(PositionDB).filter(PositionDB.position_id == position_id).first()
            if pos:
                pos.status = "CLOSED"
                pos.unrealized_pnl = 0.0
                db.commit()
        finally:
            if own_session:
                db.close()

    @staticmethod
    def update_live_position_price(position_id: str, new_price: float, db: Optional[Session] = None):
        """Updates current market price and unrealized P&L for an active position."""
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            pos = db.query(PositionDB).filter(PositionDB.position_id == position_id).first()
            if pos and pos.status == "OPEN":
                new_price = round(new_price, 2)
                pos.current_price = new_price
                pos.unrealized_pnl = round((new_price - pos.entry_price) * pos.quantity, 2)
                
                # Dynamic breakeven / trailing SL update
                gain_pct = (new_price - pos.entry_price) / pos.entry_price
                if gain_pct >= 0.08:
                    be_price = round(pos.entry_price * 1.025, 2)
                    if pos.trailing_sl is None or be_price > pos.trailing_sl:
                        pos.trailing_sl = be_price
                if gain_pct >= 0.15:
                    l1 = round(pos.entry_price * 1.08, 2)
                    if pos.trailing_sl is None or l1 > pos.trailing_sl:
                        pos.trailing_sl = l1
                if gain_pct >= 0.24:
                    l2 = round(pos.entry_price * 1.16, 2)
                    if pos.trailing_sl is None or l2 > pos.trailing_sl:
                        pos.trailing_sl = l2

                # Check auto-exit conditions
                should_exit = False
                exit_reason = ""
                if (pos.target and new_price >= pos.target) or gain_pct >= 0.30:
                    should_exit = True
                    exit_reason = "TARGET_HIT_30PCT"
                elif pos.trailing_sl and new_price <= pos.trailing_sl:
                    should_exit = True
                    exit_reason = "TRAILING_PROFIT_LOCK_HIT" if pos.trailing_sl >= pos.entry_price * 1.05 else "BREAKEVEN_PROFIT_HIT"
                elif pos.stop_loss and new_price <= pos.stop_loss:
                    should_exit = True
                    exit_reason = "STOP_LOSS_HIT"

                if should_exit:
                    now_dt = datetime.utcnow()
                    pos.status = "CLOSED"
                    pos.unrealized_pnl = 0.0
                    costs = CostCalculator.calculate(
                        buy_price=pos.entry_price,
                        sell_price=new_price,
                        quantity=pos.quantity,
                        slippage_pct=0.004
                    )
                    gross_pnl = round((new_price - pos.entry_price) * pos.quantity, 2)
                    net_pnl = round(gross_pnl - costs.total_cost, 2)
                    invested = pos.entry_price * pos.quantity
                    ret_pct = round((net_pnl / invested) * 100, 2) if invested > 0 else 0.0
                    holding_mins = max(1, int((now_dt - pos.entry_time).total_seconds() / 60))
                    import uuid
                    trade = TradeDB(
                        trade_id=str(uuid.uuid4()),
                        strategy_id=pos.strategy_id,
                        underlying=pos.underlying,
                        option_symbol=pos.option_symbol,
                        expiry_date=pos.expiry,
                        strike=pos.strike,
                        option_type=pos.option_type,
                        entry_time=pos.entry_time,
                        entry_price=pos.entry_price,
                        exit_time=now_dt,
                        exit_price=new_price,
                        quantity=pos.quantity,
                        gross_pnl=gross_pnl,
                        brokerage=costs.brokerage,
                        stt=costs.stt,
                        exchange_charges=costs.exchange_charges,
                        gst=costs.gst,
                        sebi_charges=costs.sebi_charges,
                        stamp_duty=costs.stamp_duty,
                        total_charges=costs.total_statutory_charges,
                        slippage=costs.total_slippage,
                        net_pnl=net_pnl,
                        return_pct=ret_pct,
                        entry_reason=f"SIGNAL_{pos.strategy_id}",
                        exit_reason=exit_reason,
                        signal_score=82.0,
                        market_regime="STRONG_BULLISH" if pos.option_type == "CE" else "STRONG_BEARISH",
                        holding_time_minutes=holding_mins
                    )
                    db.add(trade)
                db.commit()
        finally:
            if own_session:
                db.close()

    @staticmethod
    def open_live_paper_trade(
        strategy_id: str,
        underlying: str,
        option_symbol: str,
        option_type: str,
        strike: float,
        expiry: date,
        quantity: int,
        entry_price: float,
        stop_loss: float,
        target: float,
        db: Optional[Session] = None
    ) -> str:
        """Opens a new active live paper position in PositionDB."""
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            import uuid
            pos_id = str(uuid.uuid4())
            new_pos = PositionDB(
                position_id=pos_id,
                strategy_id=strategy_id,
                option_symbol=option_symbol,
                underlying=underlying,
                option_type=option_type,
                strike=strike,
                expiry=expiry,
                quantity=quantity,
                entry_time=datetime.utcnow(),
                entry_price=entry_price,
                current_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                trailing_sl=None,
                unrealized_pnl=0.0,
                status="OPEN"
            )
            db.add(new_pos)
            db.commit()
            return pos_id
        finally:
            if own_session:
                db.close()

    @staticmethod
    def square_off_live_position(position_id: str, exit_price: float, reason: str = "MANUAL_SQUARE_OFF", db: Optional[Session] = None):
        """Squares off open position, calculates taxes/slippage, and saves to TradeDB."""
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            from config.cost_model import CostCalculator
            pos = db.query(PositionDB).filter(PositionDB.position_id == position_id).first()
            if pos and pos.status == "OPEN":
                now_dt = datetime.utcnow()
                pos.status = "CLOSED"
                pos.current_price = exit_price
                pos.unrealized_pnl = 0.0

                costs = CostCalculator.calculate(
                    buy_price=pos.entry_price,
                    sell_price=exit_price,
                    quantity=pos.quantity,
                    slippage_pct=0.004
                )
                gross_pnl = round((exit_price - pos.entry_price) * pos.quantity, 2)
                net_pnl = round(gross_pnl - costs.total_cost, 2)
                invested = pos.entry_price * pos.quantity
                ret_pct = round((net_pnl / invested) * 100, 2) if invested > 0 else 0.0
                holding_mins = max(1, int((now_dt - pos.entry_time).total_seconds() / 60))

                import uuid
                t_id = str(uuid.uuid4())
                trade = TradeDB(
                    trade_id=t_id,
                    strategy_id=pos.strategy_id,
                    underlying=pos.underlying,
                    option_symbol=pos.option_symbol,
                    expiry_date=pos.expiry,
                    strike=pos.strike,
                    option_type=pos.option_type,
                    entry_time=pos.entry_time,
                    entry_price=pos.entry_price,
                    exit_time=now_dt,
                    exit_price=exit_price,
                    quantity=pos.quantity,
                    gross_pnl=gross_pnl,
                    brokerage=costs.brokerage,
                    stt=costs.stt,
                    exchange_charges=costs.exchange_charges,
                    gst=costs.gst,
                    sebi_charges=costs.sebi_charges,
                    stamp_duty=costs.stamp_duty,
                    total_charges=costs.total_statutory_charges,
                    slippage=costs.total_slippage,
                    net_pnl=net_pnl,
                    return_pct=ret_pct,
                    entry_reason=f"SIGNAL_{pos.strategy_id}",
                    exit_reason=reason,
                    signal_score=82.0,
                    market_regime="STRONG_BULLISH" if pos.option_type == "CE" else "STRONG_BEARISH",
                    holding_time_minutes=holding_mins
                )
                db.add(trade)
                db.commit()
                return t_id
        finally:
            if own_session:
                db.close()

    @staticmethod
    def get_signals(limit: int = 50, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            records = db.query(SignalDB).order_by(SignalDB.timestamp.desc()).limit(limit).all()
            return [
                {
                    "signal_id": r.signal_id,
                    "timestamp": r.timestamp.isoformat(),
                    "strategy_id": r.strategy_id,
                    "underlying": r.underlying,
                    "direction": r.direction,
                    "signal_score": r.signal_score,
                    "market_regime": r.market_regime,
                    "underlying_price": r.underlying_price,
                    "is_accepted": r.is_accepted,
                    "rejection_reason": r.rejection_reason
                }
                for r in records
            ]
        finally:
            if own_session:
                db.close()

    @staticmethod
    def clear_all_data(db: Optional[Session] = None):
        """Clears all historical runtime records from database tables."""
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True
        try:
            db.query(TradeDB).delete()
            db.query(PositionDB).delete()
            db.query(OrderDB).delete()
            db.query(SignalDB).delete()
            db.query(DailyPnLDB).delete()
            db.query(RiskEventDB).delete()
            db.query(SystemEventDB).delete()
            db.query(StrategyRunDB).delete()
            db.commit()
        finally:
            if own_session:
                db.close()

