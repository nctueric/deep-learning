"""Tests for token bucket rate limiter."""

import asyncio

from portfolio_tracker.gateway.rate_limiter import TokenBucketRateLimiter


async def _test_basic_acquire():
    limiter = TokenBucketRateLimiter(max_tokens=5, refill_rate=10)
    # Should acquire immediately
    await limiter.acquire(1)
    assert limiter.available_tokens < 5


async def _test_burst_limit():
    limiter = TokenBucketRateLimiter(max_tokens=3, refill_rate=100)
    await limiter.acquire(1)
    await limiter.acquire(1)
    await limiter.acquire(1)
    # 4th acquire should need to wait briefly
    assert limiter.available_tokens < 1


def test_basic_acquire():
    asyncio.run(_test_basic_acquire())


def test_burst_limit():
    asyncio.run(_test_burst_limit())
