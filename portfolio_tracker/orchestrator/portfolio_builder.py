"""Portfolio Builder — CRUD operations for user-defined portfolios.

Supports:
- Manual portfolio construction with target weights
- Import positions from IBKR account
- Portfolio templates (60/40, Tech Heavy, Dividend Income, etc.)
"""

import uuid
import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from portfolio_tracker.core.models.target_portfolio import TargetPortfolio, UserPortfolioHolding
from portfolio_tracker.core.models.instrument import Instrument
from portfolio_tracker.gateway.ibkr_client import IBKRClient

logger = logging.getLogger(__name__)

# Pre-built portfolio templates
PORTFOLIO_TEMPLATES = {
    "60/40 Stocks/Bonds": [
        {"symbol": "VTI", "weight": 0.42},   # Total US Stock Market
        {"symbol": "VXUS", "weight": 0.18},  # International Stocks
        {"symbol": "BND", "weight": 0.28},   # US Bonds
        {"symbol": "BNDX", "weight": 0.12},  # International Bonds
    ],
    "Tech Heavy": [
        {"symbol": "QQQ", "weight": 0.30},   # Nasdaq 100
        {"symbol": "AAPL", "weight": 0.15},
        {"symbol": "MSFT", "weight": 0.15},
        {"symbol": "NVDA", "weight": 0.10},
        {"symbol": "GOOGL", "weight": 0.10},
        {"symbol": "AMZN", "weight": 0.10},
        {"symbol": "META", "weight": 0.10},
    ],
    "Dividend Income": [
        {"symbol": "VYM", "weight": 0.25},   # Vanguard High Dividend Yield
        {"symbol": "SCHD", "weight": 0.25},  # Schwab US Dividend Equity
        {"symbol": "JNJ", "weight": 0.10},
        {"symbol": "PG", "weight": 0.10},
        {"symbol": "KO", "weight": 0.10},
        {"symbol": "PEP", "weight": 0.10},
        {"symbol": "O", "weight": 0.10},     # Realty Income
    ],
    "S&P 500 Core": [
        {"symbol": "SPY", "weight": 0.50},
        {"symbol": "VOO", "weight": 0.50},
    ],
}


class PortfolioBuilder:
    """Manages portfolio creation, editing, and template application."""

    async def create_portfolio(
        self, session: AsyncSession, name: str, description: str = "", targets: list[dict] | None = None
    ) -> TargetPortfolio:
        """Create a new target portfolio."""
        portfolio = TargetPortfolio(
            portfolio_id=str(uuid.uuid4()),
            name=name,
            description=description,
            targets=targets or [],
        )
        session.add(portfolio)
        await session.commit()
        await session.refresh(portfolio)
        logger.info(f"Created portfolio '{name}' with {len(targets or [])} targets")
        return portfolio

    async def create_from_template(
        self, session: AsyncSession, template_name: str, custom_name: str | None = None
    ) -> TargetPortfolio:
        """Create a portfolio from a pre-built template."""
        if template_name not in PORTFOLIO_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}. Available: {list(PORTFOLIO_TEMPLATES.keys())}")

        targets = PORTFOLIO_TEMPLATES[template_name]
        name = custom_name or template_name
        return await self.create_portfolio(session, name, f"Based on template: {template_name}", targets)

    async def import_from_ibkr(self, session: AsyncSession, ibkr_client: IBKRClient, name: str = "Imported from IBKR") -> TargetPortfolio:
        """Import current IBKR positions as a new portfolio."""
        positions = await ibkr_client.get_portfolio()
        if not positions:
            raise ValueError("No positions found in IBKR account")

        # Calculate total value for weight computation
        total_value = sum(abs(float(pos.marketValue)) for pos in positions)

        targets = []
        holdings = []
        for pos in positions:
            symbol = pos.contract.symbol
            weight = abs(float(pos.marketValue)) / total_value if total_value > 0 else 0
            targets.append({"symbol": symbol, "weight": round(weight, 4)})

            # Ensure instrument exists
            existing = await session.get(Instrument, symbol)
            if not existing:
                session.add(Instrument(
                    symbol=symbol,
                    exchange=pos.contract.exchange or "SMART",
                    currency=pos.contract.currency or "USD",
                ))

            holdings.append({
                "symbol": symbol,
                "quantity": float(pos.position),
                "avg_cost": float(pos.averageCost),
            })

        portfolio = await self.create_portfolio(session, name, "Imported from IBKR account", targets)

        # Add actual holdings
        for h in holdings:
            session.add(UserPortfolioHolding(
                portfolio_id=portfolio.portfolio_id,
                symbol=h["symbol"],
                quantity=Decimal(str(h["quantity"])),
                avg_cost=Decimal(str(h["avg_cost"])),
            ))
        await session.commit()

        logger.info(f"Imported {len(holdings)} positions from IBKR")
        return portfolio

    async def update_targets(self, session: AsyncSession, portfolio_id: str, targets: list[dict]) -> TargetPortfolio:
        """Update target allocations for a portfolio."""
        portfolio = await session.get(TargetPortfolio, portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        # Validate weights sum to ~1.0
        total_weight = sum(t["weight"] for t in targets)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Target weights sum to {total_weight:.4f}, must be ~1.0")

        portfolio.targets = targets
        portfolio.updated_at = datetime.utcnow()
        await session.commit()
        return portfolio

    async def add_holding(
        self, session: AsyncSession, portfolio_id: str, symbol: str, quantity: float, avg_cost: float
    ) -> UserPortfolioHolding:
        """Add a holding to a portfolio."""
        # Ensure instrument exists
        existing = await session.get(Instrument, symbol.upper())
        if not existing:
            session.add(Instrument(symbol=symbol.upper()))

        holding = UserPortfolioHolding(
            portfolio_id=portfolio_id,
            symbol=symbol.upper(),
            quantity=Decimal(str(quantity)),
            avg_cost=Decimal(str(avg_cost)),
        )
        session.add(holding)
        await session.commit()
        return holding

    async def remove_holding(self, session: AsyncSession, holding_id: int) -> bool:
        """Remove a holding from a portfolio."""
        holding = await session.get(UserPortfolioHolding, holding_id)
        if holding:
            await session.delete(holding)
            await session.commit()
            return True
        return False

    async def get_portfolio(self, session: AsyncSession, portfolio_id: str) -> dict:
        """Get full portfolio with targets and holdings."""
        portfolio = await session.get(TargetPortfolio, portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        result = await session.execute(
            select(UserPortfolioHolding).where(UserPortfolioHolding.portfolio_id == portfolio_id)
        )
        holdings = result.scalars().all()

        return {
            "portfolio": portfolio,
            "holdings": holdings,
            "targets": portfolio.targets,
        }

    async def list_portfolios(self, session: AsyncSession) -> list[TargetPortfolio]:
        """List all target portfolios."""
        result = await session.execute(select(TargetPortfolio))
        return list(result.scalars().all())

    @staticmethod
    def get_available_templates() -> dict[str, list[dict]]:
        return PORTFOLIO_TEMPLATES
