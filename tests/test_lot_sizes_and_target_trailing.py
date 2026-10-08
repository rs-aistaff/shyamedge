import pytest
from datetime import datetime, date
from core.constants import Underlying, StrategyID, OptionType, LOT_SIZES
from core.models import Position, Bar
from database.connection import init_db
from database.repository import Repository
from strategies.donchian_v1 import DonchianBreakoutStrategy

def test_official_exchange_lot_sizes():
    """Verify that lot sizes strictly match official exchange derivative contracts."""
    assert LOT_SIZES[Underlying.NIFTY50] == 65, "NIFTY 50 lot size must be exactly 65"
    assert LOT_SIZES[Underlying.SENSEX] == 20, "SENSEX lot size must be exactly 20"

def test_target_and_trailing_stop_auto_exit():
    """Verify that price going up triggers trailing stop ratchets and auto-exits at +30% target."""
    init_db()

    # Create test active position
    entry_p = 100.0
    sl_p = 85.0
    tgt_p = 130.0
    lot = LOT_SIZES[Underlying.NIFTY50]

    pos_id = Repository.open_live_paper_trade(
        strategy_id="DONCHIAN",
        underlying="NIFTY50",
        option_symbol="NIFTY26OCT24500CE",
        option_type="CE",
        strike=24500.0,
        expiry=date(2026, 10, 15),
        quantity=lot,
        entry_price=entry_p,
        stop_loss=sl_p,
        target=tgt_p
    )

    from database.connection import SessionLocal
    from database.models import PositionDB

    # 1. Price moves to +9% (109.0) -> Trailing SL should ratchet to Breakeven (+2.5% = 102.50)
    Repository.update_live_position_price(pos_id, 109.0)
    with SessionLocal() as db:
        pos = db.query(PositionDB).filter(PositionDB.position_id == pos_id).first()
        assert pos is not None
        assert pos.trailing_sl == 102.50

    # 2. Price moves to +16% (116.0) -> Trailing SL should ratchet to +8% (108.00)
    Repository.update_live_position_price(pos_id, 116.0)
    with SessionLocal() as db:
        pos = db.query(PositionDB).filter(PositionDB.position_id == pos_id).first()
        assert pos is not None
        assert pos.trailing_sl == 108.00

    # 3. Price moves to +25% (125.0) -> Trailing SL should ratchet to +16% (116.00)
    Repository.update_live_position_price(pos_id, 125.0)
    with SessionLocal() as db:
        pos = db.query(PositionDB).filter(PositionDB.position_id == pos_id).first()
        assert pos is not None
        assert pos.trailing_sl == 116.00

    # 4. Price moves to Target (+30% = 130.0) -> Position MUST AUTO-EXIT IMMEDIATELY
    Repository.update_live_position_price(pos_id, 131.0)
    with SessionLocal() as db:
        pos = db.query(PositionDB).filter(PositionDB.position_id == pos_id).first()
        assert pos.status == "CLOSED", "Position must be automatically closed upon reaching target"

    # Verify closed trade recorded
    trades = Repository.get_trades(limit=1)
    assert len(trades) >= 1
    latest_trade = trades[0]
    assert latest_trade["exit_reason"] == "TARGET_HIT_30PCT"
    assert latest_trade["quantity"] == 65
    assert latest_trade["net_pnl"] > 0
