"""Target portfolio and user holdings models for Portfolio Builder."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from portfolio_tracker.core.database import Base


class TargetPortfolio(Base):
    __tablename__ = "target_portfolios"

    portfolio_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    targets: Mapped[dict] = mapped_column(JSON, default=list)
    # targets structure: [{"symbol": "AAPL", "weight": 0.25}, {"symbol": "MSFT", "weight": 0.15}, ...]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class UserPortfolioHolding(Base):
    __tablename__ = "user_portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("target_portfolios.portfolio_id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("instruments.symbol"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    added_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
