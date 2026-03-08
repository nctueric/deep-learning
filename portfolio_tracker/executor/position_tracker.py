"""Real-time position tracking and available funds monitoring."""

import logging
from decimal import Decimal
from dataclasses import dataclass, field

from portfolio_tracker.gateway.ibkr_client import IBKRClient

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Current position state."""

    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    market_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    weight: Decimal = Decimal("0")  # % of portfolio


@dataclass
class AccountState:
    """Current account state."""

    net_liquidation_value: Decimal = Decimal("0")
    available_funds: Decimal = Decimal("0")
    buying_power: Decimal = Decimal("0")
    margin_used: Decimal = Decimal("0")
    daily_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    positions: list[Position] = field(default_factory=list)


class PositionTracker:
    """Tracks real-time positions and account state from IBKR."""

    def __init__(self, ibkr_client: IBKRClient):
        self.client = ibkr_client
        self._last_state: AccountState | None = None

    async def refresh(self) -> AccountState:
        """Fetch latest account state and positions from IBKR."""
        account_values = await self.client.get_account_values()
        portfolio_items = await self.client.get_portfolio()

        nlv = Decimal(account_values.get("NetLiquidation", "0"))

        positions = []
        total_unrealized = Decimal("0")
        for item in portfolio_items:
            pos = Position(
                symbol=item.contract.symbol,
                quantity=Decimal(str(item.position)),
                avg_cost=Decimal(str(item.averageCost)),
                market_price=Decimal(str(item.marketPrice)),
                market_value=Decimal(str(item.marketValue)),
                unrealized_pnl=Decimal(str(item.unrealizedPNL)),
                realized_pnl=Decimal(str(item.realizedPNL)),
                weight=Decimal(str(item.marketValue)) / nlv * 100 if nlv > 0 else Decimal("0"),
            )
            positions.append(pos)
            total_unrealized += pos.unrealized_pnl

        state = AccountState(
            net_liquidation_value=nlv,
            available_funds=Decimal(account_values.get("AvailableFunds", "0")),
            buying_power=Decimal(account_values.get("BuyingPower", "0")),
            margin_used=Decimal(account_values.get("FullMaintMarginReq", "0")),
            daily_pnl=Decimal(account_values.get("DailyPnL", "0")),
            unrealized_pnl=total_unrealized,
            positions=positions,
        )
        self._last_state = state
        return state

    @property
    def last_state(self) -> AccountState | None:
        return self._last_state

    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol."""
        if not self._last_state:
            return None
        for pos in self._last_state.positions:
            if pos.symbol == symbol.upper():
                return pos
        return None

    def get_sector_exposure(self) -> dict[str, Decimal]:
        """Get exposure by sector (placeholder — requires sector mapping data)."""
        # In production, this would map symbols to GICS sectors
        exposure: dict[str, Decimal] = {}
        if self._last_state:
            for pos in self._last_state.positions:
                exposure[pos.symbol] = pos.weight
        return exposure
