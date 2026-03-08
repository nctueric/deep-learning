"""Portfolio model that manages holdings and transactions."""

from datetime import datetime
from typing import Optional

from portfolio_tracker.models.holding import Holding
from portfolio_tracker.models.transaction import Transaction, TransactionType


class Portfolio:
    """Manages a collection of holdings and records transactions."""

    def __init__(self, name: str = "My Portfolio"):
        self.name = name
        self.holdings: dict[str, Holding] = {}
        self.transactions: list[Transaction] = []

    def buy(self, symbol: str, quantity: float, price: float, timestamp: Optional[datetime] = None) -> Transaction:
        """Record a buy transaction and update holdings."""
        symbol = symbol.upper()
        tx = Transaction(
            symbol=symbol,
            transaction_type=TransactionType.BUY,
            quantity=quantity,
            price=price,
            timestamp=timestamp or datetime.now(),
        )
        self.transactions.append(tx)

        if symbol in self.holdings:
            h = self.holdings[symbol]
            total_cost = h.total_cost + tx.total_value
            h.quantity += quantity
            h.avg_cost = total_cost / h.quantity
            h.updated_at = tx.timestamp
        else:
            self.holdings[symbol] = Holding(
                symbol=symbol,
                quantity=quantity,
                avg_cost=price,
                created_at=tx.timestamp,
                updated_at=tx.timestamp,
            )

        return tx

    def sell(self, symbol: str, quantity: float, price: float, timestamp: Optional[datetime] = None) -> Transaction:
        """Record a sell transaction and update holdings."""
        symbol = symbol.upper()
        if symbol not in self.holdings:
            raise ValueError(f"No holding found for {symbol}")

        h = self.holdings[symbol]
        if quantity > h.quantity:
            raise ValueError(f"Cannot sell {quantity} shares of {symbol}, only {h.quantity} available")

        tx = Transaction(
            symbol=symbol,
            transaction_type=TransactionType.SELL,
            quantity=quantity,
            price=price,
            timestamp=timestamp or datetime.now(),
        )
        self.transactions.append(tx)

        h.quantity -= quantity
        h.updated_at = tx.timestamp

        if h.quantity == 0:
            del self.holdings[symbol]

        return tx

    def total_cost_basis(self) -> float:
        """Total cost basis across all holdings."""
        return sum(h.total_cost for h in self.holdings.values())

    def total_market_value(self, prices: dict[str, float]) -> float:
        """Total market value given current prices."""
        return sum(
            h.market_value(prices.get(h.symbol, h.avg_cost))
            for h in self.holdings.values()
        )

    def total_gain_loss(self, prices: dict[str, float]) -> float:
        """Total unrealized gain/loss."""
        return self.total_market_value(prices) - self.total_cost_basis()

    def summary(self, prices: dict[str, float]) -> dict:
        """Generate a portfolio summary."""
        holdings_summary = []
        for symbol, h in sorted(self.holdings.items()):
            current_price = prices.get(symbol, h.avg_cost)
            holdings_summary.append({
                "symbol": symbol,
                "quantity": h.quantity,
                "avg_cost": h.avg_cost,
                "current_price": current_price,
                "market_value": h.market_value(current_price),
                "gain_loss": h.gain_loss(current_price),
                "gain_loss_pct": h.gain_loss_pct(current_price),
            })

        total_cost = self.total_cost_basis()
        total_value = self.total_market_value(prices)
        total_gl = total_value - total_cost
        total_gl_pct = (total_gl / total_cost * 100) if total_cost > 0 else 0.0

        return {
            "name": self.name,
            "holdings": holdings_summary,
            "total_cost_basis": total_cost,
            "total_market_value": total_value,
            "total_gain_loss": total_gl,
            "total_gain_loss_pct": total_gl_pct,
            "num_holdings": len(self.holdings),
            "num_transactions": len(self.transactions),
        }

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "holdings": {s: h.to_dict() for s, h in self.holdings.items()},
            "transactions": [t.to_dict() for t in self.transactions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        p = cls(name=data["name"])
        p.holdings = {s: Holding.from_dict(h) for s, h in data["holdings"].items()}
        p.transactions = [Transaction.from_dict(t) for t in data["transactions"]]
        return p
