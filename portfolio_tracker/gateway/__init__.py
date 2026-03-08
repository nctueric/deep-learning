# Lazy imports to avoid requiring ib_async at import time
from portfolio_tracker.gateway.rate_limiter import TokenBucketRateLimiter

__all__ = ["IBKRClient", "TokenBucketRateLimiter", "DataStreamer", "AccountSync"]


def __getattr__(name):
    if name == "IBKRClient":
        from portfolio_tracker.gateway.ibkr_client import IBKRClient
        return IBKRClient
    if name == "DataStreamer":
        from portfolio_tracker.gateway.data_streamer import DataStreamer
        return DataStreamer
    if name == "AccountSync":
        from portfolio_tracker.gateway.account_sync import AccountSync
        return AccountSync
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
