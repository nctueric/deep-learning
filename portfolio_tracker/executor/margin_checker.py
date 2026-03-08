"""Pre-trade margin check and leverage validation.

Safety mechanisms (per ib_strategy_project):
- Atomic margin check via IBKR whatIfOrder
- 0.3x gradual leverage adjustment steps
- 3x emergency liquidation trigger
"""

import logging
from dataclasses import dataclass
from decimal import Decimal

from portfolio_tracker.config.settings import settings
from portfolio_tracker.gateway.ibkr_client import IBKRClient

logger = logging.getLogger(__name__)


@dataclass
class MarginCheckResult:
    """Result of pre-trade margin validation."""

    passed: bool
    current_leverage: Decimal
    projected_leverage: Decimal
    leverage_change: Decimal
    available_margin: Decimal
    order_margin_impact: Decimal
    message: str
    emergency_liquidation: bool = False


class MarginChecker:
    """Validates orders against margin constraints before submission."""

    def __init__(self, ibkr_client: IBKRClient):
        self.client = ibkr_client
        self.cfg = settings.risk

    async def check(self, contract, order) -> MarginCheckResult:
        """Run pre-trade margin check using IBKR's whatIfOrder."""
        try:
            what_if = await self.client.what_if_order(contract, order)
        except Exception as e:
            return MarginCheckResult(
                passed=False,
                current_leverage=Decimal("0"),
                projected_leverage=Decimal("0"),
                leverage_change=Decimal("0"),
                available_margin=Decimal("0"),
                order_margin_impact=Decimal("0"),
                message=f"Margin check failed: {e}",
            )

        # Extract margin values
        init_margin = Decimal(str(getattr(what_if, "initMarginChange", 0) or 0))
        maint_margin = Decimal(str(getattr(what_if, "maintMarginChange", 0) or 0))
        equity = Decimal(str(getattr(what_if, "equityWithLoanAfter", 0) or 0))

        # Calculate leverage
        account_values = await self.client.get_account_values()
        nlv = Decimal(account_values.get("NetLiquidation", "1"))
        current_margin = Decimal(account_values.get("FullMaintMarginReq", "0"))
        current_leverage = current_margin / nlv if nlv > 0 else Decimal("0")

        projected_margin = current_margin + maint_margin
        projected_leverage = projected_margin / nlv if nlv > 0 else Decimal("0")
        leverage_change = projected_leverage - current_leverage

        # Check emergency liquidation threshold
        if projected_leverage >= Decimal(str(self.cfg.max_leverage)):
            return MarginCheckResult(
                passed=False,
                current_leverage=current_leverage,
                projected_leverage=projected_leverage,
                leverage_change=leverage_change,
                available_margin=equity,
                order_margin_impact=init_margin,
                message=f"EMERGENCY: Projected leverage {projected_leverage:.2f}x exceeds {self.cfg.max_leverage}x limit",
                emergency_liquidation=True,
            )

        # Check gradual leverage step
        if abs(leverage_change) > Decimal(str(self.cfg.leverage_step)):
            return MarginCheckResult(
                passed=False,
                current_leverage=current_leverage,
                projected_leverage=projected_leverage,
                leverage_change=leverage_change,
                available_margin=equity,
                order_margin_impact=init_margin,
                message=(
                    f"Leverage change {leverage_change:.2f}x exceeds {self.cfg.leverage_step}x step limit. "
                    f"Reduce order size for gradual adjustment."
                ),
            )

        return MarginCheckResult(
            passed=True,
            current_leverage=current_leverage,
            projected_leverage=projected_leverage,
            leverage_change=leverage_change,
            available_margin=equity,
            order_margin_impact=init_margin,
            message=f"Margin check passed. Leverage: {current_leverage:.2f}x → {projected_leverage:.2f}x",
        )
