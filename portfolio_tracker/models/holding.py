"""Model representing a single holding in a portfolio."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Holding:
    """Represents a stock/asset holding with quantity and cost basis."""

    symbol: str
    quantity: float
    avg_cost: float
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_cost(self) -> float:
        """Total cost basis for this holding."""
        return self.quantity * self.avg_cost

    def market_value(self, current_price: float) -> float:
        """Calculate current market value."""
        return self.quantity * current_price

    def gain_loss(self, current_price: float) -> float:
        """Calculate unrealized gain/loss."""
        return self.market_value(current_price) - self.total_cost

    def gain_loss_pct(self, current_price: float) -> float:
        """Calculate unrealized gain/loss percentage."""
        if self.total_cost == 0:
            return 0.0
        return (self.gain_loss(current_price) / self.total_cost) * 100

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_cost": self.avg_cost,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Holding":
        return cls(
            symbol=data["symbol"],
            quantity=data["quantity"],
            avg_cost=data["avg_cost"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
