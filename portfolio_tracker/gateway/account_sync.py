"""Periodic account state synchronization and snapshot persistence."""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

from portfolio_tracker.gateway.ibkr_client import IBKRClient

logger = logging.getLogger(__name__)


class AccountSync:
    """Syncs IBKR account state and creates portfolio snapshots."""

    def __init__(self, ibkr_client: IBKRClient):
        self.client = ibkr_client
        self._sync_task: asyncio.Task | None = None

    async def get_account_state(self) -> dict:
        """Fetch current account state from IBKR."""
        values = await self.client.get_account_values()
        positions = await self.client.get_portfolio()

        positions_data = []
        for pos in positions:
            positions_data.append({
                "symbol": pos.contract.symbol,
                "quantity": float(pos.position),
                "avg_cost": float(pos.averageCost),
                "market_value": float(pos.marketValue),
                "unrealized_pnl": float(pos.unrealizedPNL),
                "realized_pnl": float(pos.realizedPNL),
            })

        return {
            "net_liquidation_value": Decimal(values.get("NetLiquidation", "0")),
            "available_funds": Decimal(values.get("AvailableFunds", "0")),
            "margin_usage": Decimal(values.get("FullMaintMarginReq", "0")),
            "buying_power": Decimal(values.get("BuyingPower", "0")),
            "daily_pnl": Decimal(values.get("DailyPnL", "0")),
            "positions": positions_data,
        }

    async def take_snapshot(self, session=None) -> dict:
        """Take a portfolio snapshot and optionally persist to DB."""
        state = await self.get_account_state()

        if session:
            from portfolio_tracker.core.models.snapshot import PortfolioSnapshot
            snapshot = PortfolioSnapshot(
                timestamp=datetime.utcnow(),
                net_liquidation_value=state["net_liquidation_value"],
                available_funds=state["available_funds"],
                margin_usage=state["margin_usage"],
                positions_data=state["positions"],
            )
            session.add(snapshot)
            await session.commit()
            logger.info(f"Snapshot saved: NLV={state['net_liquidation_value']}")

        return state

    async def start_periodic_sync(self, interval_seconds: int = 60, session_factory=None):
        """Start background task to periodically sync account state."""
        async def _sync_loop():
            while True:
                try:
                    if session_factory:
                        async with session_factory() as session:
                            await self.take_snapshot(session)
                    else:
                        await self.take_snapshot()
                except Exception as e:
                    logger.error(f"Account sync error: {e}")
                await asyncio.sleep(interval_seconds)

        self._sync_task = asyncio.create_task(_sync_loop())
        logger.info(f"Started periodic account sync (every {interval_seconds}s)")

    async def stop_periodic_sync(self):
        if self._sync_task:
            self._sync_task.cancel()
            self._sync_task = None
