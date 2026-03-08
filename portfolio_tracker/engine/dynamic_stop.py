"""ATR-based dynamic stop-loss calculator.

Stop Price = Entry Price - (M × ATR_n)

Where M is the volatility multiplier (default 2.0, range [1.5, 3.0]).
High volatility → wider stop (avoid noise whipsaw)
Low volatility → tighter stop (protect unrealized gains)
"""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from portfolio_tracker.config.settings import settings
from portfolio_tracker.engine.indicators import TechnicalIndicators


@dataclass
class StopResult:
    """Result of dynamic stop-loss calculation."""

    symbol: str
    entry_price: Decimal
    atr_value: Decimal
    multiplier: Decimal
    stop_distance: Decimal
    stop_price: Decimal
    stop_pct: Decimal  # Distance as percentage of entry


class DynamicStopCalculator:
    """Computes ATR-based dynamic stop-loss levels."""

    def __init__(self):
        self.indicators = TechnicalIndicators()

    def calculate(
        self,
        symbol: str,
        entry_price: float,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        multiplier: float | None = None,
        atr_period: int | None = None,
    ) -> StopResult:
        """Calculate dynamic stop-loss price based on ATR."""
        cfg = settings.risk
        m = multiplier or cfg.atr_multiplier_default
        m = max(cfg.atr_multiplier_min, min(cfg.atr_multiplier_max, m))
        period = atr_period or cfg.atr_period

        atr_series = self.indicators.compute_atr(high, low, close, period)
        latest_atr = float(atr_series[~np.isnan(atr_series)][-1]) if len(atr_series[~np.isnan(atr_series)]) > 0 else 0

        stop_distance = m * latest_atr
        stop_price = entry_price - stop_distance
        stop_pct = (stop_distance / entry_price * 100) if entry_price > 0 else 0

        return StopResult(
            symbol=symbol,
            entry_price=Decimal(str(entry_price)),
            atr_value=Decimal(str(round(latest_atr, 6))),
            multiplier=Decimal(str(m)),
            stop_distance=Decimal(str(round(stop_distance, 6))),
            stop_price=Decimal(str(round(stop_price, 2))),
            stop_pct=Decimal(str(round(stop_pct, 2))),
        )

    def calculate_from_atr(
        self,
        symbol: str,
        entry_price: float,
        atr_value: float,
        multiplier: float | None = None,
    ) -> StopResult:
        """Calculate stop-loss from a pre-computed ATR value."""
        cfg = settings.risk
        m = multiplier or cfg.atr_multiplier_default
        m = max(cfg.atr_multiplier_min, min(cfg.atr_multiplier_max, m))

        stop_distance = m * atr_value
        stop_price = entry_price - stop_distance
        stop_pct = (stop_distance / entry_price * 100) if entry_price > 0 else 0

        return StopResult(
            symbol=symbol,
            entry_price=Decimal(str(entry_price)),
            atr_value=Decimal(str(round(atr_value, 6))),
            multiplier=Decimal(str(m)),
            stop_distance=Decimal(str(round(stop_distance, 6))),
            stop_price=Decimal(str(round(stop_price, 2))),
            stop_pct=Decimal(str(round(stop_pct, 2))),
        )
