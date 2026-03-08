"""Execution model — IBKR execution reports (fill confirmations)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from portfolio_tracker.core.database import Base


class Execution(Base):
    __tablename__ = "executions"

    exec_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    internal_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.internal_order_id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("instruments.symbol"), nullable=False)
    exec_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    exec_qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
