"""Instrument model — static reference data for tradeable assets."""

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from portfolio_tracker.core.database import Base


class Instrument(Base):
    __tablename__ = "instruments"

    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    exchange: Mapped[str] = mapped_column(String(20), default="SMART")
    asset_class: Mapped[str] = mapped_column(String(20), default="STK")
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    multiplier: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
