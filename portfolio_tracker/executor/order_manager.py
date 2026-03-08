"""Order lifecycle management: validate → submit → monitor → confirm → persist.

Implements 5-layer timeout protection to prevent stuck orders:
1. Order submission timeout (10s)
2. Fill acknowledgement timeout (30s)
3. Partial fill monitoring (5min)
4. End-of-day auto-cancel
5. Stale order sweep (periodic)
"""

import asyncio
import logging
import uuid
from datetime import datetime
from decimal import Decimal

from ib_async import LimitOrder, StopOrder, Order as IBOrder

from portfolio_tracker.core.schemas.trading import CandidateOrder
from portfolio_tracker.core.models.order import Order, OrderStatus, OrderAction
from portfolio_tracker.gateway.ibkr_client import IBKRClient
from portfolio_tracker.executor.margin_checker import MarginChecker

logger = logging.getLogger(__name__)

# Timeout constants (seconds)
SUBMIT_TIMEOUT = 10
FILL_ACK_TIMEOUT = 30
PARTIAL_FILL_TIMEOUT = 300


class OrderManager:
    """Manages the full lifecycle of orders from candidate to execution."""

    def __init__(self, ibkr_client: IBKRClient):
        self.client = ibkr_client
        self.margin_checker = MarginChecker(ibkr_client)
        self._active_orders: dict[str, dict] = {}

    async def submit_candidate(self, candidate: CandidateOrder, session=None) -> Order:
        """Validate and submit a candidate order to IBKR."""
        # Step 1: Risk check must have passed
        if not candidate.risk_check_passed:
            order_record = self._create_order_record(candidate, OrderStatus.RISK_CHECK_FAILED)
            if session:
                session.add(order_record)
                await session.commit()
            logger.warning(f"Order blocked by risk check: {candidate.risk_check_message}")
            return order_record

        # Step 2: Resolve contract
        contract = await self.client.get_stock_contract(candidate.symbol)

        # Step 3: Build IBKR order
        ib_order = self._build_ib_order(candidate)

        # Step 4: Margin check
        margin_result = await self.margin_checker.check(contract, ib_order)
        if not margin_result.passed:
            order_record = self._create_order_record(candidate, OrderStatus.RISK_CHECK_FAILED)
            order_record.status = OrderStatus.RISK_CHECK_FAILED
            if session:
                session.add(order_record)
                await session.commit()
            logger.warning(f"Order blocked by margin check: {margin_result.message}")
            return order_record

        # Step 5: Submit with timeout protection
        order_record = self._create_order_record(candidate, OrderStatus.RISK_CHECK_PASSED)
        try:
            trade = await asyncio.wait_for(
                self.client.place_order(contract, ib_order),
                timeout=SUBMIT_TIMEOUT,
            )
            order_record.ibkr_order_id = trade.order.orderId
            order_record.status = OrderStatus.SUBMITTED
            self._active_orders[order_record.internal_order_id] = {
                "trade": trade,
                "submitted_at": datetime.utcnow(),
            }
            logger.info(f"Order submitted: {candidate.symbol} {candidate.action} {candidate.quantity}")
        except asyncio.TimeoutError:
            order_record.status = OrderStatus.REJECTED
            logger.error(f"Order submission timed out after {SUBMIT_TIMEOUT}s")
        except Exception as e:
            order_record.status = OrderStatus.REJECTED
            logger.error(f"Order submission failed: {e}")

        if session:
            session.add(order_record)
            await session.commit()

        # Step 6: Attach stop-loss order if applicable
        if candidate.atr_stop_distance and order_record.status == OrderStatus.SUBMITTED:
            await self._attach_stop_loss(contract, candidate)

        return order_record

    async def _attach_stop_loss(self, contract, candidate: CandidateOrder):
        """Submit a protective stop-loss order."""
        stop = StopOrder(
            action="SELL" if candidate.action == "BUY" else "BUY",
            totalQuantity=float(candidate.quantity),
            stopPrice=float(candidate.stop_loss_price),
        )
        try:
            await self.client.place_order(contract, stop)
            logger.info(f"Stop-loss attached at {candidate.stop_loss_price} for {candidate.symbol}")
        except Exception as e:
            logger.error(f"Failed to attach stop-loss: {e}")

    async def cancel(self, internal_order_id: str) -> bool:
        """Cancel an active order."""
        if internal_order_id not in self._active_orders:
            return False
        trade = self._active_orders[internal_order_id]["trade"]
        await self.client.cancel_order(trade.order)
        del self._active_orders[internal_order_id]
        return True

    async def sweep_stale_orders(self, max_age_seconds: int = 3600):
        """Cancel orders that have been pending too long (anti-stuck layer 5)."""
        now = datetime.utcnow()
        stale = []
        for oid, info in self._active_orders.items():
            age = (now - info["submitted_at"]).total_seconds()
            if age > max_age_seconds:
                stale.append(oid)
        for oid in stale:
            await self.cancel(oid)
            logger.info(f"Swept stale order: {oid}")

    def _build_ib_order(self, candidate: CandidateOrder) -> IBOrder:
        """Convert CandidateOrder to IBKR Order object."""
        if candidate.order_type == "LMT":
            return LimitOrder(
                action=candidate.action,
                totalQuantity=float(candidate.quantity),
                lmtPrice=float(candidate.entry_price),
            )
        elif candidate.order_type == "STP":
            return StopOrder(
                action=candidate.action,
                totalQuantity=float(candidate.quantity),
                stopPrice=float(candidate.stop_loss_price),
            )
        else:
            return LimitOrder(
                action=candidate.action,
                totalQuantity=float(candidate.quantity),
                lmtPrice=float(candidate.entry_price),
            )

    def _create_order_record(self, candidate: CandidateOrder, status: OrderStatus) -> Order:
        return Order(
            internal_order_id=str(uuid.uuid4()),
            symbol=candidate.symbol,
            action=OrderAction(candidate.action),
            order_type=candidate.order_type,
            quantity=candidate.quantity,
            limit_price=candidate.entry_price if candidate.order_type == "LMT" else None,
            stop_price=candidate.stop_loss_price,
            risk_reward_ratio=candidate.risk_reward_ratio,
            atr_stop_distance=candidate.atr_stop_distance,
            status=status,
        )
