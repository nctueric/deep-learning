"""Real-time data streaming from IBKR to PostgreSQL and Redis."""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal

from portfolio_tracker.gateway.ibkr_client import IBKRClient

logger = logging.getLogger(__name__)


class DataStreamer:
    """Subscribes to IBKR real-time data, normalizes, and persists to storage."""

    def __init__(self, ibkr_client: IBKRClient):
        self.client = ibkr_client
        self._subscriptions: dict[str, asyncio.Task] = {}
        self._redis = None

    async def init_redis(self):
        """Initialize Redis connection for quote caching."""
        try:
            import redis.asyncio as aioredis
            from portfolio_tracker.config.settings import settings
            self._redis = aioredis.from_url(settings.redis.url)
        except ImportError:
            logger.warning("redis package not available, caching disabled")

    async def subscribe_bars(self, symbol: str, exchange: str = "SMART"):
        """Subscribe to real-time 5-second bars for a symbol."""
        contract = await self.client.get_stock_contract(symbol, exchange)
        bars = await self.client.get_realtime_bars(contract)

        async def _process_bars():
            async for bar in bars:
                await self._on_bar(symbol, bar)

        task = asyncio.create_task(_process_bars())
        self._subscriptions[symbol] = task
        logger.info(f"Subscribed to real-time bars for {symbol}")

    async def _on_bar(self, symbol: str, bar):
        """Process incoming bar data."""
        bar_data = {
            "symbol": symbol,
            "timestamp": str(bar.time),
            "open": float(bar.open_),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": int(bar.volume),
        }

        # Cache latest quote in Redis
        if self._redis:
            from portfolio_tracker.config.settings import settings
            await self._redis.setex(
                f"quote:{symbol}",
                settings.redis.quote_ttl,
                json.dumps(bar_data),
            )

    async def fetch_and_store_historical(
        self,
        symbol: str,
        duration: str = "1 Y",
        bar_size: str = "1 day",
        session=None,
    ) -> int:
        """Fetch historical data from IBKR and store in PostgreSQL."""
        contract = await self.client.get_stock_contract(symbol)
        bars = await self.client.get_historical_bars(contract, duration, bar_size)

        if session is None:
            logger.info(f"Fetched {len(bars)} bars for {symbol} (no DB session, skipping persist)")
            return len(bars)

        from portfolio_tracker.core.models.ohlcv import HistoricalOHLCV

        timeframe_map = {"1 day": "1D", "1 hour": "1h", "15 mins": "15m", "5 mins": "5m", "1 min": "1m"}
        tf = timeframe_map.get(bar_size, bar_size)

        count = 0
        for bar in bars:
            ohlcv = HistoricalOHLCV(
                symbol=symbol,
                timestamp=bar.date,
                timeframe=tf,
                open=Decimal(str(bar.open)),
                high=Decimal(str(bar.high)),
                low=Decimal(str(bar.low)),
                close=Decimal(str(bar.close)),
                volume=int(bar.volume),
            )
            session.add(ohlcv)
            count += 1

        await session.commit()
        logger.info(f"Stored {count} historical bars for {symbol}")
        return count

    async def unsubscribe(self, symbol: str):
        """Cancel real-time subscription for a symbol."""
        if symbol in self._subscriptions:
            self._subscriptions[symbol].cancel()
            del self._subscriptions[symbol]

    async def unsubscribe_all(self):
        """Cancel all subscriptions."""
        for task in self._subscriptions.values():
            task.cancel()
        self._subscriptions.clear()

    async def get_cached_quote(self, symbol: str) -> dict | None:
        """Get latest cached quote from Redis."""
        if self._redis:
            data = await self._redis.get(f"quote:{symbol}")
            if data:
                return json.loads(data)
        return None
