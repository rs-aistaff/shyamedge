from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from config.settings import settings
from database.connection import init_db
from database.repository import Repository
from risk_engine.kill_switch import KillSwitchManager
from paper_engine.runner import PaperTradingRunner
from core.constants import Underlying

app = FastAPI(
    title="ShyamEdge Options Buying Algo Engine",
    description="Algorithmic Research & Paper-Trading Platform for NIFTY 50 and SENSEX Options Buying (₹15,000 Portfolio)",
    version="1.0.0"
)

# Global runner instance
runner = PaperTradingRunner(underlying=Underlying.NIFTY50)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def get_health() -> Dict[str, Any]:
    return {
        "status": "HEALTHY",
        "app_mode": settings.app_mode.value,
        "is_running": runner.is_running,
        "kill_switch_active": KillSwitchManager.is_active(),
        "initial_capital": settings.initial_capital,
        "current_capital": runner.portfolio.current_capital,
        "daily_realized_pnl": runner.portfolio.daily_realized_pnl,
        "daily_loss_limit_hit": runner.portfolio.daily_loss_limit_hit
    }

@app.get("/signals")
def get_signals(limit: int = 50) -> List[Dict[str, Any]]:
    # In SQLite/Postgres repository
    from database.connection import SessionLocal
    from database.models import SignalDB
    db = SessionLocal()
    try:
        rows = db.query(SignalDB).order_by(SignalDB.timestamp.desc()).limit(limit).all()
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
            for r in rows
        ]
    finally:
        db.close()

@app.get("/positions")
def get_positions() -> Dict[str, Any]:
    pos = runner.portfolio.active_position
    if not pos:
        return {"has_open_position": False, "position": None}
    return {
        "has_open_position": True,
        "position": {
            "position_id": str(pos.position_id),
            "strategy_id": pos.strategy_id.value,
            "option_symbol": pos.option_symbol,
            "underlying": pos.underlying.value,
            "quantity": pos.quantity,
            "entry_time": pos.entry_time.isoformat(),
            "entry_price": pos.entry_price,
            "stop_loss": pos.stop_loss,
            "target": pos.target
        }
    }

@app.get("/trades")
def get_trades(limit: int = 50, strategy_id: Optional[str] = None) -> List[Dict[str, Any]]:
    return Repository.get_trades(limit=limit, strategy_id=strategy_id)

@app.get("/pnl")
def get_pnl() -> Dict[str, Any]:
    return {
        "initial_capital": runner.portfolio.initial_capital,
        "current_capital": runner.portfolio.current_capital,
        "cash_available": runner.portfolio.cash,
        "daily_realized_pnl": runner.portfolio.daily_realized_pnl,
        "max_drawdown": runner.portfolio.max_drawdown,
        "daily_trade_count": runner.portfolio.daily_trade_count,
        "daily_loss_limit_hit": runner.portfolio.daily_loss_limit_hit
    }

@app.get("/strategies")
def get_strategies() -> Dict[str, Any]:
    return runner.portfolio.strategy_stats

@app.post("/paper/start")
def start_paper() -> Dict[str, str]:
    runner.start()
    return {"status": "SUCCESS", "message": "Paper trading runner active"}

@app.post("/paper/stop")
def stop_paper() -> Dict[str, str]:
    runner.stop()
    return {"status": "SUCCESS", "message": "Paper trading runner stopped"}

class KillSwitchPayload(BaseModel):
    action: str  # "ACTIVATE" or "DEACTIVATE"
    reason: str = "Manual override"

@app.post("/kill-switch")
def toggle_kill_switch(payload: KillSwitchPayload) -> Dict[str, Any]:
    if payload.action.upper() == "ACTIVATE":
        KillSwitchManager.activate(payload.reason)
        # Force square-off active position if any
        pos = runner.portfolio.active_position
        if pos:
            runner._execute_exit(pos, pos.stop_loss, "KILL_SWITCH_EMERGENCY_EXIT", runner.portfolio.current_date, "EMERGENCY")
        return {"kill_switch": "ACTIVE", "message": f"Kill switch triggered: {payload.reason}"}
    else:
        KillSwitchManager.deactivate()
        return {"kill_switch": "INACTIVE", "message": "Kill switch deactivated"}
