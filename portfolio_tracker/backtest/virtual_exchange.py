"""Virtual Exchange — state machine matching engine with slippage and commission models.

Simulates real exchange behavior:
- Order state machine: PENDING → SUBMITTED → FILLED/CANCELLED
- Slippage penalty based on volume and order size
- IBKR tiered commission model
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from portfolio_tracker.backtest.data_replay import MarketEvent


class VirtualOrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    STOP_TRIGGERED = "STOP_TRIGGERED"


@dataclass
class VirtualOrder:
    """An order in the virtual exchange."""

    order_id: int
    symbol: str
    action: str  # BUY or SELL
    quantity: float
    limit_price: float | None = None
    stop_price: float | None = None
    status: VirtualOrderStatus = VirtualOrderStatus.PENDING
    fill_price: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0


@dataclass
class VirtualPosition:
    """A position in the virtual portfolio."""

    symbol: str
    quantity: float = 0.0
    avg_cost: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class VirtualExchange:
    """Simulates order matching with slippage and commission."""

    cash: float = 100000.0
    commission_per_share: float = 0.005  # IBKR tiered: $0.005/share
    min_commission: float = 1.0
    slippage_bps: float = 5.0  # 5 basis points default slippage

    _positions: dict[str, VirtualPosition] = field(default_factory=dict)
    _pending_orders: list[VirtualOrder] = field(default_factory=list)
    _filled_orders: list[VirtualOrder] = field(default_factory=list)
    _next_order_id: int = 1

    def submit_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> VirtualOrder:
        """Submit an order to the virtual exchange."""
        order = VirtualOrder(
            order_id=self._next_order_id,
            symbol=symbol,
            action=action.upper(),
            quantity=quantity,
            limit_price=limit_price,
            stop_price=stop_price,
        )
        self._next_order_id += 1
        self._pending_orders.append(order)
        return order

    def process_event(self, event: MarketEvent) -> list[VirtualOrder]:
        """Process a market event and fill eligible orders."""
        filled = []
        remaining = []

        for order in self._pending_orders:
            if order.symbol != event.symbol:
                remaining.append(order)
                continue

            fill_price = self._try_fill(order, event)
            if fill_price is not None:
                # Apply slippage
                slippage = fill_price * (self.slippage_bps / 10000)
                if order.action == "BUY":
                    fill_price += slippage
                else:
                    fill_price -= slippage

                # Calculate commission
                commission = max(self.min_commission, order.quantity * self.commission_per_share)

                order.fill_price = fill_price
                order.slippage = slippage * order.quantity
                order.commission = commission
                order.status = VirtualOrderStatus.FILLED

                # Update position and cash
                self._execute_fill(order)
                filled.append(order)
                self._filled_orders.append(order)
            else:
                remaining.append(order)

        self._pending_orders = remaining
        return filled

    def _try_fill(self, order: VirtualOrder, event: MarketEvent) -> float | None:
        """Check if an order can be filled at this event's prices."""
        if order.stop_price is not None:
            # Stop order: triggered when price crosses stop level
            if order.action == "SELL" and event.low <= order.stop_price:
                return order.stop_price
            if order.action == "BUY" and event.high >= order.stop_price:
                return order.stop_price
            return None

        if order.limit_price is not None:
            # Limit order: filled if price reaches limit
            if order.action == "BUY" and event.low <= order.limit_price:
                return order.limit_price
            if order.action == "SELL" and event.high >= order.limit_price:
                return order.limit_price
            return None

        # Market order: filled at close
        return event.close

    def _execute_fill(self, order: VirtualOrder):
        """Update positions and cash after a fill."""
        if order.symbol not in self._positions:
            self._positions[order.symbol] = VirtualPosition(symbol=order.symbol)

        pos = self._positions[order.symbol]
        cost = order.fill_price * order.quantity + order.commission

        if order.action == "BUY":
            total_cost = pos.avg_cost * pos.quantity + order.fill_price * order.quantity
            pos.quantity += order.quantity
            pos.avg_cost = total_cost / pos.quantity if pos.quantity > 0 else 0
            self.cash -= cost
        else:  # SELL
            pnl = (order.fill_price - pos.avg_cost) * order.quantity - order.commission
            pos.realized_pnl += pnl
            pos.quantity -= order.quantity
            self.cash += order.fill_price * order.quantity - order.commission

            if pos.quantity <= 0:
                pos.quantity = 0
                pos.avg_cost = 0

    @property
    def positions(self) -> dict[str, VirtualPosition]:
        return self._positions

    @property
    def filled_orders(self) -> list[VirtualOrder]:
        return self._filled_orders

    def portfolio_value(self, prices: dict[str, float]) -> float:
        """Calculate total portfolio value (cash + positions)."""
        pos_value = sum(
            pos.quantity * prices.get(pos.symbol, pos.avg_cost)
            for pos in self._positions.values()
        )
        return self.cash + pos_value

    def total_realized_pnl(self) -> float:
        return sum(pos.realized_pnl for pos in self._positions.values())

    def total_commission(self) -> float:
        return sum(o.commission for o in self._filled_orders)
