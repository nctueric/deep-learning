"""Tests for ATR-based dynamic stop-loss calculator."""

import numpy as np
from decimal import Decimal

from portfolio_tracker.engine.dynamic_stop import DynamicStopCalculator


def test_stop_below_entry_for_long():
    calc = DynamicStopCalculator()
    np.random.seed(42)
    n = 50
    close = np.cumsum(np.random.randn(n)) + 150
    high = close + np.abs(np.random.randn(n)) * 2
    low = close - np.abs(np.random.randn(n)) * 2

    result = calc.calculate("AAPL", entry_price=150.0, high=high, low=low, close=close, multiplier=2.0)

    assert result.stop_price < Decimal("150")
    assert result.atr_value > 0
    assert result.stop_distance > 0
    assert result.stop_pct > 0


def test_multiplier_clamped_to_range():
    calc = DynamicStopCalculator()
    close = np.ones(20) * 100
    high = close + 2
    low = close - 2

    # Multiplier below min (1.5) should be clamped
    result_low = calc.calculate("TEST", 100.0, high, low, close, multiplier=0.5)
    result_high = calc.calculate("TEST", 100.0, high, low, close, multiplier=10.0)

    assert result_low.multiplier == Decimal("1.5")
    assert result_high.multiplier == Decimal("3.0")


def test_from_precomputed_atr():
    calc = DynamicStopCalculator()
    result = calc.calculate_from_atr("AAPL", entry_price=200.0, atr_value=5.0, multiplier=2.0)

    assert result.stop_price == Decimal("190.0")
    assert result.stop_distance == Decimal("10.0")
    assert result.atr_value == Decimal("5.0")
