"""Async IBKR client wrapper using ib_async with auto-reconnect."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from ib_async import IB, Contract, Stock, BarData, PortfolioItem, AccountValue

from portfolio_tracker.config.settings import settings
from portfolio_tracker.gateway.rate_limiter import (
    TokenBucketRateLimiter,
    create_global_limiter,
    create_historical_limiter,
)

logger = logging.getLogger(__name__)


class IBKRClient:
    """High-level async wrapper around ib_async with rate limiting and auto-reconnect."""

    def __init__(self):
        self.ib = IB()
        self._global_limiter = create_global_limiter()
        self._hist_limiter = create_historical_limiter()
        self._connected = False
        self._reconnect_task: asyncio.Task | None = None

    async def connect(self) -> None:
        """Establish connection to TWS/IB Gateway."""
        cfg = settings.ibkr
        await self.ib.connectAsync(
            host=cfg.host,
            port=cfg.port,
            clientId=cfg.client_id,
            timeout=cfg.timeout,
            readonly=cfg.readonly,
        )
        self._connected = True
        self.ib.disconnectedEvent += self._on_disconnect
        logger.info(f"Connected to IBKR at {cfg.host}:{cfg.port} (client {cfg.client_id})")

    def _on_disconnect(self):
        """Handle unexpected disconnection with auto-reconnect."""
        self._connected = False
        logger.warning("IBKR connection lost, scheduling reconnect...")
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._auto_reconnect())

    async def _auto_reconnect(self, max_retries: int = 5):
        """Exponential backoff reconnection."""
        for attempt in range(max_retries):
            wait = 2 ** attempt
            logger.info(f"Reconnect attempt {attempt + 1}/{max_retries} in {wait}s...")
            await asyncio.sleep(wait)
            try:
                await self.connect()
                logger.info("Reconnected successfully")
                return
            except Exception as e:
                logger.error(f"Reconnect failed: {e}")
        logger.critical(f"Failed to reconnect after {max_retries} attempts")

    async def disconnect(self) -> None:
        self.ib.disconnect()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.ib.isConnected()

    # --- Market Data ---

    async def get_stock_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
        """Resolve a stock contract via IBKR."""
        await self._global_limiter.acquire()
        contract = Stock(symbol, exchange, currency)
        qualified = await self.ib.qualifyContractsAsync(contract)
        return qualified[0] if qualified else contract

    async def get_historical_bars(
        self,
        contract: Contract,
        duration: str = "1 Y",
        bar_size: str = "1 day",
        what_to_show: str = "TRADES",
    ) -> list[BarData]:
        """Fetch historical OHLCV bars with rate limiting."""
        await self._hist_limiter.acquire()
        await self._global_limiter.acquire()
        bars = await self.ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=True,
            formatDate=1,
        )
        return bars

    async def get_realtime_bars(self, contract: Contract) -> AsyncIterator:
        """Subscribe to 5-second real-time bars."""
        await self._global_limiter.acquire()
        bars = self.ib.reqRealTimeBars(contract, barSize=5, whatToShow="TRADES", useRTH=True)
        return bars

    async def get_ticker(self, contract: Contract):
        """Request market data snapshot."""
        await self._global_limiter.acquire()
        ticker = self.ib.reqMktData(contract, genericTickList="", snapshot=True)
        await asyncio.sleep(2)  # Wait for snapshot data
        return ticker

    # --- Account ---

    async def get_account_summary(self) -> list[AccountValue]:
        """Get account summary values."""
        await self._global_limiter.acquire()
        return self.ib.accountSummary()

    async def get_portfolio(self) -> list[PortfolioItem]:
        """Get current portfolio positions."""
        await self._global_limiter.acquire()
        return self.ib.portfolio()

    async def get_account_values(self) -> dict[str, str]:
        """Get account values as a dictionary."""
        summary = await self.get_account_summary()
        return {item.tag: item.value for item in summary}

    # --- Orders ---

    async def place_order(self, contract: Contract, order) -> None:
        """Submit an order to IBKR."""
        await self._global_limiter.acquire()
        trade = self.ib.placeOrder(contract, order)
        return trade

    async def cancel_order(self, order) -> None:
        """Cancel a pending order."""
        await self._global_limiter.acquire()
        self.ib.cancelOrder(order)

    async def get_open_orders(self) -> list:
        """Get all open orders."""
        await self._global_limiter.acquire()
        return self.ib.openOrders()

    async def what_if_order(self, contract: Contract, order) -> dict:
        """Simulate order for margin impact (pre-trade check)."""
        await self._global_limiter.acquire()
        result = await self.ib.whatIfOrderAsync(contract, order)
        return result


@asynccontextmanager
async def get_ibkr_client():
    """Context manager for IBKR client lifecycle."""
    client = IBKRClient()
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()
