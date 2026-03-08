"""Candidate order factory — combines R/R check + ATR stop into validated trade proposals."""

import numpy as np
from decimal import Decimal

from portfolio_tracker.core.schemas.trading import CandidateOrder
from portfolio_tracker.engine.risk_reward import RiskRewardCalculator
from portfolio_tracker.engine.dynamic_stop import DynamicStopCalculator


class CandidateOrderFactory:
    """Creates and validates candidate orders with integrated risk checks."""

    def __init__(self):
        self.rr_calc = RiskRewardCalculator()
        self.stop_calc = DynamicStopCalculator()

    def create_with_manual_stop(
        self,
        symbol: str,
        action: str,
        quantity: float,
        entry_price: float,
        stop_loss_price: float,
        target_price: float,
        order_type: str = "LMT",
    ) -> CandidateOrder:
        """Create a candidate order with user-specified stop and target."""
        rr_result = self.rr_calc.calculate(entry_price, stop_loss_price, target_price)

        return CandidateOrder(
            symbol=symbol.upper(),
            action=action.upper(),
            quantity=Decimal(str(quantity)),
            entry_price=Decimal(str(entry_price)),
            stop_loss_price=Decimal(str(stop_loss_price)),
            target_price=Decimal(str(target_price)),
            order_type=order_type,
            risk_reward_ratio=rr_result.ratio,
            risk_check_passed=rr_result.passed,
            risk_check_message=rr_result.message,
        )

    def create_with_atr_stop(
        self,
        symbol: str,
        action: str,
        quantity: float,
        entry_price: float,
        target_price: float,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        atr_multiplier: float | None = None,
        order_type: str = "LMT",
    ) -> CandidateOrder:
        """Create a candidate order with ATR-computed stop-loss."""
        stop_result = self.stop_calc.calculate(
            symbol=symbol,
            entry_price=entry_price,
            high=high,
            low=low,
            close=close,
            multiplier=atr_multiplier,
        )

        rr_result = self.rr_calc.calculate(
            entry_price, float(stop_result.stop_price), target_price
        )

        return CandidateOrder(
            symbol=symbol.upper(),
            action=action.upper(),
            quantity=Decimal(str(quantity)),
            entry_price=Decimal(str(entry_price)),
            stop_loss_price=stop_result.stop_price,
            target_price=Decimal(str(target_price)),
            order_type=order_type,
            risk_reward_ratio=rr_result.ratio,
            atr_value=stop_result.atr_value,
            atr_stop_distance=stop_result.stop_distance,
            risk_check_passed=rr_result.passed,
            risk_check_message=rr_result.message,
        )
