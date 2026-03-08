"""Tests for technical indicator calculations."""

import numpy as np

from portfolio_tracker.engine.indicators import TechnicalIndicators


def test_sma_calculation():
    indicators = TechnicalIndicators()
    close = np.array([10.0, 11.0, 12.0, 13.0, 14.0], dtype=float)
    high = close + 1
    low = close - 1

    result = indicators.compute_all("TEST", high, low, close)

    assert result.symbol == "TEST"
    # SMA 50 and 200 should be NaN for short arrays
    assert result.sma_50 is not None


def test_ema_calculation():
    indicators = TechnicalIndicators()
    close = np.arange(1, 30, dtype=float)
    high = close + 1
    low = close - 1

    result = indicators.compute_all("TEST", high, low, close)

    assert result.ema_12 is not None
    assert result.ema_26 is not None
    assert len(result.ema_12) == len(close)


def test_atr_calculation():
    indicators = TechnicalIndicators()
    np.random.seed(42)
    n = 50
    close = np.cumsum(np.random.randn(n)) + 100
    high = close + np.abs(np.random.randn(n)) * 2
    low = close - np.abs(np.random.randn(n)) * 2

    atr = indicators.compute_atr(high, low, close, period=14)

    assert len(atr) == n
    # ATR should be positive where not NaN
    valid = atr[~np.isnan(atr)]
    assert all(v >= 0 for v in valid)


def test_vwap_calculation():
    indicators = TechnicalIndicators()
    close = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    high = close + 1
    low = close - 1
    volume = np.array([1000, 1500, 2000, 1200, 1800], dtype=float)

    result = indicators.compute_all("TEST", high, low, close, volume)

    assert result.vwap is not None
    assert len(result.vwap) == len(close)
    # VWAP is a cumulative average — it should stay within the overall price range
    assert all(result.vwap[i] >= min(low) and result.vwap[i] <= max(high) for i in range(len(close)))
