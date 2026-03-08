"""Risk/Reward Ratio calculator with configurable threshold enforcement.

R/R = Potential Reward / Potential Risk
    = |Target - Entry| / |Entry - StopLoss|

System enforces minimum R/R (default 2.0) on all candidate orders.
"""

from dataclasses import dataclass
from decimal import Decimal

from portfolio_tracker.config.settings import settings


@dataclass
class RiskRewardResult:
    """Result of a risk/reward ratio calculation."""

    entry_price: Decimal
    stop_loss_price: Decimal
    target_price: Decimal
    potential_risk: Decimal
    potential_reward: Decimal
    ratio: Decimal
    threshold: Decimal
    passed: bool
    message: str


class RiskRewardCalculator:
    """Calculates and enforces risk/reward ratio constraints."""

    def __init__(self, min_ratio: float | None = None):
        self.min_ratio = Decimal(str(min_ratio or settings.risk.min_risk_reward_ratio))

    def calculate(
        self,
        entry_price: float | Decimal,
        stop_loss_price: float | Decimal,
        target_price: float | Decimal,
    ) -> RiskRewardResult:
        """Calculate risk/reward ratio and check against threshold."""
        entry = Decimal(str(entry_price))
        stop = Decimal(str(stop_loss_price))
        target = Decimal(str(target_price))

        potential_risk = abs(entry - stop)
        potential_reward = abs(target - entry)

        if potential_risk == 0:
            return RiskRewardResult(
                entry_price=entry,
                stop_loss_price=stop,
                target_price=target,
                potential_risk=potential_risk,
                potential_reward=potential_reward,
                ratio=Decimal("0"),
                threshold=self.min_ratio,
                passed=False,
                message="Stop loss equals entry price — infinite risk with zero defined downside",
            )

        ratio = potential_reward / potential_risk
        passed = ratio >= self.min_ratio

        if passed:
            message = f"R/R {ratio:.2f} >= {self.min_ratio} — trade meets risk criteria"
        else:
            message = (
                f"R/R {ratio:.2f} < {self.min_ratio} — trade BLOCKED. "
                f"Expected reward ({potential_reward:.2f}) insufficient for risk ({potential_risk:.2f})"
            )

        return RiskRewardResult(
            entry_price=entry,
            stop_loss_price=stop,
            target_price=target,
            potential_risk=potential_risk,
            potential_reward=potential_reward,
            ratio=ratio,
            threshold=self.min_ratio,
            passed=passed,
            message=message,
        )
