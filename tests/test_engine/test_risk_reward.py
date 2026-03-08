"""Tests for risk/reward ratio calculator."""

from decimal import Decimal

from portfolio_tracker.engine.risk_reward import RiskRewardCalculator


def test_rr_ratio_passes_above_threshold():
    calc = RiskRewardCalculator(min_ratio=2.0)
    result = calc.calculate(entry_price=100, stop_loss_price=95, target_price=115)

    assert result.ratio == Decimal("3")  # 15/5 = 3.0
    assert result.passed is True
    assert result.potential_risk == Decimal("5")
    assert result.potential_reward == Decimal("15")


def test_rr_ratio_fails_below_threshold():
    calc = RiskRewardCalculator(min_ratio=2.0)
    result = calc.calculate(entry_price=100, stop_loss_price=95, target_price=107)

    assert result.ratio == Decimal("1.4")  # 7/5 = 1.4
    assert result.passed is False
    assert "BLOCKED" in result.message


def test_rr_ratio_exact_threshold():
    calc = RiskRewardCalculator(min_ratio=2.0)
    result = calc.calculate(entry_price=100, stop_loss_price=95, target_price=110)

    assert result.ratio == Decimal("2")  # 10/5 = 2.0
    assert result.passed is True


def test_rr_zero_risk():
    calc = RiskRewardCalculator(min_ratio=2.0)
    result = calc.calculate(entry_price=100, stop_loss_price=100, target_price=110)

    assert result.passed is False
    assert "zero" in result.message.lower() or "equals" in result.message.lower()


def test_rr_custom_threshold():
    calc = RiskRewardCalculator(min_ratio=3.0)
    result = calc.calculate(entry_price=100, stop_loss_price=95, target_price=115)

    assert result.ratio == Decimal("3")
    assert result.passed is True

    result2 = calc.calculate(entry_price=100, stop_loss_price=95, target_price=112)
    assert result2.passed is False  # 12/5 = 2.4 < 3.0
