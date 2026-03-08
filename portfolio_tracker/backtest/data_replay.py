"""Data Replay Simulator — replays historical OHLCV as a simulated event stream.

Reads from PostgreSQL historical_ohlcv or in-memory arrays to simulate
IBKR's real-time data feed, event by event, with an internal clock.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator

import numpy as np


@dataclass
class MarketEvent:
    """A single market data event in the replay stream."""

    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class DataReplaySimulator:
    """Replays historical data as sequential market events."""

    symbols: list[str]
    _data: dict[str, list[MarketEvent]] = field(default_factory=dict)
    _current_time: datetime | None = None

    def load_from_arrays(
        self,
        symbol: str,
        timestamps: list[datetime],
        open_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        volumes: np.ndarray,
    ):
        """Load data from NumPy arrays (for testing or in-memory backtests)."""
        events = []
        for i in range(len(timestamps)):
            events.append(MarketEvent(
                timestamp=timestamps[i],
                symbol=symbol,
                open=float(open_prices[i]),
                high=float(high_prices[i]),
                low=float(low_prices[i]),
                close=float(close_prices[i]),
                volume=int(volumes[i]),
            ))
        self._data[symbol] = events

    def replay(self) -> Iterator[MarketEvent]:
        """Yield market events in chronological order across all symbols.

        This simulates the IBKR tick-by-tick data feed.
        Events are strictly ordered by timestamp to prevent look-ahead bias.
        """
        # Merge all symbol events into a single sorted stream
        all_events = []
        for events in self._data.values():
            all_events.extend(events)
        all_events.sort(key=lambda e: e.timestamp)

        for event in all_events:
            self._current_time = event.timestamp
            yield event

    @property
    def current_time(self) -> datetime | None:
        return self._current_time

    def get_data_range(self, symbol: str) -> tuple[datetime, datetime] | None:
        """Get the date range for a symbol's data."""
        events = self._data.get(symbol)
        if not events:
            return None
        return events[0].timestamp, events[-1].timestamp
