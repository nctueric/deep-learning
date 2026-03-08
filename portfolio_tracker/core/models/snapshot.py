"""Portfolio snapshot model — daily account state with JSONB positions."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column

from portfolio_tracker.core.database import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    snapshot_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    net_liquidation_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    available_funds: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    margin_usage: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)
    positions_data: Mapped[dict] = mapped_column(JSON, default=dict)
    # positions_data structure:
    # [{"symbol": "AAPL", "quantity": 100, "avg_cost": 150.0, "market_value": 17500.0, "unrealized_pnl": 2500.0}, ...]
