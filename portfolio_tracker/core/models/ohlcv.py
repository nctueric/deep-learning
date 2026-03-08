"""Historical OHLCV model — time-series price data with BRIN index."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, BigInteger, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from portfolio_tracker.core.database import Base


class HistoricalOHLCV(Base):
    __tablename__ = "historical_ohlcv"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("instruments.symbol"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)  # 1m, 5m, 15m, 1h, 1D
    open: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, default=0)

    __table_args__ = (
        # BRIN index for time-series range queries (vastly more efficient than B-Tree for ordered inserts)
        Index("ix_ohlcv_timestamp_brin", "timestamp", postgresql_using="brin"),
        Index("ix_ohlcv_symbol_timeframe", "symbol", "timeframe"),
    )
