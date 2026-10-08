from datetime import datetime
from typing import Optional, List, Dict, Any
from core.constants import OrderSide, OrderType, OrderStatus, PositionStatus
from core.models import Order, Position, Trade, Signal
from config.cost_model import CostCalculator
from broker.base import BrokerInterface
from risk_engine.portfolio import VirtualPortfolio
from database.repository import Repository

class PaperBroker(BrokerInterface):
    """
    Realistic paper trading execution broker.
    Applies configurable adverse bid-ask slippage, SEBI statutory charges,
    and updates the unified ₹15,000 virtual portfolio.
    """
    def __init__(
        self,
        portfolio: VirtualPortfolio,
        slippage_pct: float = 0.004,
        tick_size: float = 0.05
    ):
        self.portfolio = portfolio
        self.slippage_pct = slippage_pct
        self.tick_size = tick_size
        self.orders: List[Order] = []
        self.trades: List[Trade] = []

    def buy(
        self,
        symbol: str,
        quantity: int,
        requested_price: float,
        stop_loss: float,
        target: float,
        signal: Optional[Signal] = None,
        dt: Optional[datetime] = None,
        **kwargs
    ) -> Order:
        exec_time = dt or datetime.utcnow()

        # Simulate adverse slippage on buy (buyer pays slightly more)
        slip_per_unit = max(self.tick_size, round(requested_price * self.slippage_pct, 2))
        fill_price = round(requested_price + slip_per_unit, 2)
        total_slippage = round(slip_per_unit * quantity, 2)

        order = Order(
            signal_id=signal.signal_id if signal else None,
            timestamp=exec_time,
            option_symbol=symbol,
            order_side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity,
            requested_price=requested_price,
            executed_price=fill_price,
            slippage=total_slippage,
            status=OrderStatus.FILLED
        )
        self.orders.append(order)

        # Create active Position
        if signal:
            pos = Position(
                strategy_id=signal.strategy_id,
                option_symbol=symbol,
                underlying=signal.underlying,
                option_type=signal.metadata.get("option_type", "CE"),
                strike=signal.suggested_strike or 0.0,
                expiry=signal.suggested_expiry or exec_time.date(),
                quantity=quantity,
                entry_time=exec_time,
                entry_price=fill_price,
                current_price=fill_price,
                stop_loss=stop_loss,
                target=target,
                status=PositionStatus.OPEN
            )
            self.portfolio.register_entry(pos)
            Repository.save_or_update_position(pos)

        return order

    def sell(
        self,
        symbol: str,
        quantity: int,
        requested_price: float,
        reason: str,
        dt: Optional[datetime] = None,
        **kwargs
    ) -> Order:
        exec_time = dt or datetime.utcnow()

        # Simulate adverse slippage on sell (seller receives slightly less)
        slip_per_unit = max(self.tick_size, round(requested_price * self.slippage_pct, 2))
        fill_price = max(self.tick_size, round(requested_price - slip_per_unit, 2))
        total_slippage = round(slip_per_unit * quantity, 2)

        order = Order(
            timestamp=exec_time,
            option_symbol=symbol,
            order_side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity,
            requested_price=requested_price,
            executed_price=fill_price,
            slippage=total_slippage,
            status=OrderStatus.FILLED
        )
        self.orders.append(order)

        pos = self.portfolio.active_position
        if pos and pos.option_symbol == symbol:
            # Calculate itemized round-trip costs and statutory taxes
            cost_details = CostCalculator.calculate(
                buy_price=pos.entry_price,
                sell_price=fill_price,
                quantity=quantity,
                slippage_pct=self.slippage_pct,
                tick_size=self.tick_size
            )

            gross_pnl = round((fill_price - pos.entry_price) * quantity, 2)
            net_pnl = round(gross_pnl - cost_details.total_cost, 2)
            invested = pos.entry_price * quantity
            return_pct = round((net_pnl / invested) * 100, 2) if invested > 0 else 0.0
            holding_mins = max(1, int((exec_time - pos.entry_time).total_seconds() / 60))

            trade = Trade(
                strategy_id=pos.strategy_id,
                strategy_version="v1.0",
                underlying=pos.underlying,
                option_symbol=pos.option_symbol,
                expiry_date=pos.expiry,
                strike=pos.strike,
                option_type=pos.option_type,
                entry_time=pos.entry_time,
                entry_price=pos.entry_price,
                exit_time=exec_time,
                exit_price=fill_price,
                quantity=quantity,
                gross_pnl=gross_pnl,
                brokerage=cost_details.brokerage,
                stt=cost_details.stt,
                exchange_charges=cost_details.exchange_charges,
                gst=cost_details.gst,
                sebi_charges=cost_details.sebi_charges,
                stamp_duty=cost_details.stamp_duty,
                total_charges=cost_details.total_statutory_charges,
                slippage=cost_details.total_slippage,
                net_pnl=net_pnl,
                return_pct=return_pct,
                entry_reason=f"SIGNAL_SCORE_APPROVED",
                exit_reason=reason,
                signal_score=80.0,
                market_regime=kwargs.get("regime", "STRONG_BULLISH"),
                holding_time_minutes=holding_mins
            )

            # Record in repository and update virtual portfolio
            self.trades.append(trade)
            Repository.record_trade(trade)
            Repository.close_position(str(pos.position_id))
            self.portfolio.register_exit(trade)

        return order

    def get_open_positions(self) -> List[Position]:
        if self.portfolio.active_position:
            return [self.portfolio.active_position]
        return []
