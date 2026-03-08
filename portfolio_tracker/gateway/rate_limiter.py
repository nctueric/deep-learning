"""Token Bucket rate limiter for IBKR API pacing constraints.

IBKR enforces:
- Global: max 50 messages/second
- Historical data: max 60 requests per 10 minutes
"""

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class TokenBucketRateLimiter:
    """Token bucket algorithm for rate limiting API requests."""

    max_tokens: float
    refill_rate: float  # tokens per second
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    def __post_init__(self):
        self._tokens = self.max_tokens
        self._last_refill = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.max_tokens, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    async def acquire(self, tokens: float = 1.0):
        """Wait until enough tokens are available, then consume them."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
            # Wait proportional to deficit
            wait_time = (tokens - self._tokens) / self.refill_rate
            await asyncio.sleep(max(0.01, wait_time))

    @property
    def available_tokens(self) -> float:
        self._refill()
        return self._tokens


# Pre-configured limiters per IBKR pacing rules
def create_global_limiter() -> TokenBucketRateLimiter:
    """50 messages/second global limit."""
    return TokenBucketRateLimiter(max_tokens=50, refill_rate=50)


def create_historical_limiter() -> TokenBucketRateLimiter:
    """60 requests per 10 minutes for historical data."""
    return TokenBucketRateLimiter(max_tokens=60, refill_rate=60 / 600)
