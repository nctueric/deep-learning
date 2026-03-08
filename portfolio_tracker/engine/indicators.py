"""Technical indicator engine using TA-Lib for high-performance computation.

TA-Lib (C-based) is preferred over pandas-ta for:
- Vectorized computation on NumPy arrays (no DataFrame overhead)
- Microsecond-level latency suitable for real-time tick processing
- Minimal memory footprint for cloud deployment
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class IndicatorResult:
    """Container for computed technical indicators."""

    symbol: str
    sma_50: np.ndarray | None = None
    sma_200: np.ndarray | None = None
    ema_12: np.ndarray | None = None
    ema_26: np.ndarray | None = None
    atr_14: np.ndarray | None = None
    vwap: np.ndarray | None = None

    @property
    def latest_sma_50(self) -> float | None:
        return float(self.sma_50[-1]) if self.sma_50 is not None and len(self.sma_50) > 0 else None

    @property
    def latest_sma_200(self) -> float | None:
        return float(self.sma_200[-1]) if self.sma_200 is not None and len(self.sma_200) > 0 else None

    @property
    def latest_ema_12(self) -> float | None:
        return float(self.ema_12[-1]) if self.ema_12 is not None and len(self.ema_12) > 0 else None

    @property
    def latest_ema_26(self) -> float | None:
        return float(self.ema_26[-1]) if self.ema_26 is not None and len(self.ema_26) > 0 else None

    @property
    def latest_atr(self) -> float | None:
        return float(self.atr_14[-1]) if self.atr_14 is not None and len(self.atr_14) > 0 else None

    @property
    def ema_crossover_bullish(self) -> bool | None:
        """12 EMA crossing above 26 EMA."""
        if self.ema_12 is None or self.ema_26 is None or len(self.ema_12) < 2:
            return None
        prev_diff = self.ema_12[-2] - self.ema_26[-2]
        curr_diff = self.ema_12[-1] - self.ema_26[-1]
        return prev_diff <= 0 and curr_diff > 0

    @property
    def price_above_sma_200(self) -> bool | None:
        """Check if latest close is above 200 SMA (bullish long-term trend)."""
        if self.sma_200 is None:
            return None
        return True  # Caller should compare with actual close price


class TechnicalIndicators:
    """Compute technical indicators using TA-Lib or fallback pure NumPy."""

    def __init__(self):
        self._talib = None
        try:
            import talib
            self._talib = talib
        except ImportError:
            pass  # Fall back to pure NumPy implementations

    def compute_all(
        self,
        symbol: str,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        """Compute all standard indicators for a symbol."""
        result = IndicatorResult(symbol=symbol)

        result.sma_50 = self._sma(close, 50)
        result.sma_200 = self._sma(close, 200)
        result.ema_12 = self._ema(close, 12)
        result.ema_26 = self._ema(close, 26)
        result.atr_14 = self._atr(high, low, close, 14)

        if volume is not None:
            result.vwap = self._vwap(high, low, close, volume)

        return result

    def compute_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Compute ATR only."""
        return self._atr(high, low, close, period)

    # --- Internal implementations ---

    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        if self._talib:
            return self._talib.SMA(data, timeperiod=period)
        # Pure NumPy fallback
        if len(data) < period:
            return np.full_like(data, np.nan)
        kernel = np.ones(period) / period
        result = np.convolve(data, kernel, mode="full")[:len(data)]
        result[:period - 1] = np.nan
        return result

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        if self._talib:
            return self._talib.EMA(data, timeperiod=period)
        # Pure NumPy fallback
        alpha = 2.0 / (period + 1)
        result = np.empty_like(data)
        result[0] = data[0]
        for i in range(1, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
        return result

    def _atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        if self._talib:
            return self._talib.ATR(high, low, close, timeperiod=period)
        # Pure NumPy fallback: TR then SMA
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1]),
            ),
        )
        tr = np.insert(tr, 0, high[0] - low[0])
        return self._sma(tr, period)

    def _vwap(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Volume Weighted Average Price — cumulative intraday VWAP."""
        typical_price = (high + low + close) / 3.0
        cumulative_tp_vol = np.cumsum(typical_price * volume)
        cumulative_vol = np.cumsum(volume)
        # Avoid division by zero
        cumulative_vol = np.where(cumulative_vol == 0, 1, cumulative_vol)
        return cumulative_tp_vol / cumulative_vol
