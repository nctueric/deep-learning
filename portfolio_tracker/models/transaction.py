"""Model representing a buy/sell transaction."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Transaction:
    """Records a single buy or sell transaction."""

    symbol: str
    transaction_type: TransactionType
    quantity: float
    price: float
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_value(self) -> float:
        return self.quantity * self.price

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "transaction_type": self.transaction_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            symbol=data["symbol"],
            transaction_type=TransactionType(data["transaction_type"]),
            quantity=data["quantity"],
            price=data["price"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
