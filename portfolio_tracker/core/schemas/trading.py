"""Pydantic schemas for trading operations."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CandidateOrder(BaseModel):
    """A proposed trade that must pass risk checks before execution."""

    symbol: str
    action: str  # BUY or SELL
    quantity: Decimal
    entry_price: Decimal
    stop_loss_price: Decimal
    target_price: Decimal
    order_type: str = "LMT"

    # Computed by risk engine
    risk_reward_ratio: Decimal | None = None
    atr_value: Decimal | None = None
    atr_stop_distance: Decimal | None = None
    risk_check_passed: bool = False
    risk_check_message: str = ""

    @property
    def potential_risk(self) -> Decimal:
        return abs(self.entry_price - self.stop_loss_price)

    @property
    def potential_reward(self) -> Decimal:
        return abs(self.target_price - self.entry_price)


class OrderPreview(BaseModel):
    """Pre-trade risk calculation result shown to user before execution."""

    symbol: str
    action: str
    quantity: Decimal
    entry_price: Decimal
    stop_loss_price: Decimal
    target_price: Decimal
    risk_reward_ratio: Decimal
    atr_value: Decimal
    estimated_slippage: Decimal = Decimal("0")
    estimated_commission: Decimal = Decimal("0")
    max_potential_loss: Decimal
    risk_check_passed: bool
    risk_check_message: str


class PortfolioSummary(BaseModel):
    """Current portfolio overview."""

    net_liquidation_value: Decimal
    available_funds: Decimal
    margin_usage: Decimal
    daily_pnl: Decimal
    unrealized_pnl: Decimal
    positions: list[dict]
    timestamp: datetime


class RebalanceAction(BaseModel):
    """A single rebalance action: buy or sell to reach target weight."""

    symbol: str
    action: str  # BUY or SELL
    quantity: Decimal
    current_weight: Decimal
    target_weight: Decimal
    weight_diff: Decimal
    estimated_value: Decimal


class RebalancePlan(BaseModel):
    """Full rebalance plan comparing current vs target allocation."""

    portfolio_id: str
    total_value: Decimal
    actions: list[RebalanceAction]
    total_buy_value: Decimal = Decimal("0")
    total_sell_value: Decimal = Decimal("0")
