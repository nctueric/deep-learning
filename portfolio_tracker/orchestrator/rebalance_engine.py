"""Rebalance engine — compare actual vs target weights, generate candidate orders.

All generated orders are CandidateOrders that must pass through
the risk engine (R/R check, margin check) before execution.
"""

import logging
from decimal import Decimal

from portfolio_tracker.core.schemas.trading import RebalanceAction, RebalancePlan
from portfolio_tracker.executor.position_tracker import AccountState

logger = logging.getLogger(__name__)


class RebalanceEngine:
    """Computes rebalance actions to align portfolio with target allocation."""

    def compute_rebalance_plan(
        self,
        portfolio_id: str,
        targets: list[dict],
        account_state: AccountState,
        prices: dict[str, float],
        tolerance_pct: float = 1.0,
    ) -> RebalancePlan:
        """Generate a rebalance plan based on target vs actual weights.

        Args:
            portfolio_id: ID of the target portfolio
            targets: List of {"symbol": "AAPL", "weight": 0.25}
            account_state: Current account state with positions
            prices: Current market prices per symbol
            tolerance_pct: Weight drift tolerance before action (default 1%)
        """
        total_value = account_state.net_liquidation_value
        if total_value <= 0:
            return RebalancePlan(portfolio_id=portfolio_id, total_value=Decimal("0"), actions=[])

        # Build current weight map from positions
        current_weights: dict[str, Decimal] = {}
        for pos in account_state.positions:
            current_weights[pos.symbol] = pos.weight / 100  # Convert from % to fraction

        # Build target weight map
        target_weights: dict[str, Decimal] = {}
        for t in targets:
            target_weights[t["symbol"]] = Decimal(str(t["weight"]))

        actions = []
        total_buy = Decimal("0")
        total_sell = Decimal("0")

        # Process each target symbol
        all_symbols = set(list(target_weights.keys()) + list(current_weights.keys()))
        for symbol in sorted(all_symbols):
            target_w = target_weights.get(symbol, Decimal("0"))
            current_w = current_weights.get(symbol, Decimal("0"))
            diff = target_w - current_w

            # Skip if within tolerance
            if abs(diff) * 100 <= Decimal(str(tolerance_pct)):
                continue

            price = Decimal(str(prices.get(symbol, 0)))
            if price <= 0:
                logger.warning(f"No price available for {symbol}, skipping")
                continue

            # Calculate shares to trade
            target_value = total_value * diff
            quantity = abs(target_value / price)

            action_type = "BUY" if diff > 0 else "SELL"
            estimated_value = quantity * price

            if action_type == "BUY":
                total_buy += estimated_value
            else:
                total_sell += estimated_value

            actions.append(RebalanceAction(
                symbol=symbol,
                action=action_type,
                quantity=quantity.quantize(Decimal("0.01")),
                current_weight=current_w,
                target_weight=target_w,
                weight_diff=diff,
                estimated_value=estimated_value.quantize(Decimal("0.01")),
            ))

        return RebalancePlan(
            portfolio_id=portfolio_id,
            total_value=total_value,
            actions=actions,
            total_buy_value=total_buy.quantize(Decimal("0.01")),
            total_sell_value=total_sell.quantize(Decimal("0.01")),
        )
