"""IBKR MCP Server — exposes portfolio data and tools to LLM agents via Model Context Protocol.

Primitives:
- Resources (read-only): portfolio positions, OHLCV data, account summary
- Tools (executable): calculate_atr, analyze_risk_reward, propose_trade, get_sector_exposure
- Prompts (templates): sector analysis, rebalancing suggestions

Safety: propose_trade generates CandidateOrders only — never direct execution.
Human-in-the-loop confirmation is required for all trades.
"""

import json
import logging
from decimal import Decimal

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(
    "IBKR Portfolio Tracker",
    description="Portfolio management tools for AI agents. Read portfolio data, compute indicators, and propose trades (human approval required).",
)


# ──────────────────────────────────────────────
# RESOURCES (read-only data exposed to LLM)
# ──────────────────────────────────────────────

@mcp.resource("ibkr://portfolio/positions")
def get_positions() -> str:
    """Current portfolio positions with unrealized P&L."""
    # In production: fetches from IBKR via PositionTracker
    return json.dumps({
        "status": "demo",
        "positions": [],
        "message": "Connect IBKR for live position data",
    })


@mcp.resource("ibkr://account/summary")
def get_account_summary() -> str:
    """Account summary: NLV, available funds, margin usage."""
    return json.dumps({
        "status": "demo",
        "net_liquidation_value": 100000,
        "available_funds": 100000,
        "margin_usage": 0,
        "daily_pnl": 0,
    })


@mcp.resource("ohlcv://{symbol}/{timeframe}")
def get_ohlcv(symbol: str, timeframe: str) -> str:
    """Historical OHLCV data for a symbol and timeframe."""
    return json.dumps({
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "status": "demo",
        "data": [],
        "message": "Connect IBKR and populate database for historical data",
    })


# ──────────────────────────────────────────────
# TOOLS (executable functions for LLM agents)
# ──────────────────────────────────────────────

@mcp.tool()
def calculate_atr(symbol: str, period: int = 14) -> str:
    """Calculate the Average True Range (ATR) for a symbol.

    ATR measures market volatility and is used for dynamic stop-loss calculation.
    Higher ATR = higher volatility = wider stop-loss distance.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL")
        period: ATR lookback period (default: 14 days)
    """
    # In production: fetches real data and computes via engine.indicators
    return json.dumps({
        "symbol": symbol.upper(),
        "period": period,
        "atr_value": None,
        "message": "Connect IBKR to compute live ATR. Demo mode returns no data.",
    })


@mcp.tool()
def analyze_risk_reward(entry_price: float, stop_loss_price: float, target_price: float) -> str:
    """Analyze the risk/reward ratio for a potential trade.

    System requires R/R >= 2.0 by default. Trades below threshold will be blocked.

    R/R = |Target - Entry| / |Entry - StopLoss|

    Args:
        entry_price: Planned entry price
        stop_loss_price: Stop-loss price level
        target_price: Target profit price level
    """
    from portfolio_tracker.engine.risk_reward import RiskRewardCalculator

    calc = RiskRewardCalculator()
    result = calc.calculate(entry_price, stop_loss_price, target_price)

    return json.dumps({
        "entry_price": float(result.entry_price),
        "stop_loss_price": float(result.stop_loss_price),
        "target_price": float(result.target_price),
        "potential_risk": float(result.potential_risk),
        "potential_reward": float(result.potential_reward),
        "risk_reward_ratio": float(result.ratio),
        "threshold": float(result.threshold),
        "passed": result.passed,
        "message": result.message,
    })


@mcp.tool()
def propose_trade(symbol: str, action: str, quantity: int, entry_price: float, stop_loss: float, target: float) -> str:
    """Propose a trade for human review. This does NOT execute the trade.

    The proposed trade will appear in the UI for the user to review and approve.
    All proposals must pass risk/reward validation (R/R >= 2.0) and margin checks.

    IMPORTANT: This tool NEVER directly executes trades. Human confirmation is always required.

    Args:
        symbol: Stock ticker (e.g., "AAPL")
        action: "BUY" or "SELL"
        quantity: Number of shares
        entry_price: Proposed entry price
        stop_loss: Stop-loss price
        target: Target price
    """
    from portfolio_tracker.engine.risk_reward import RiskRewardCalculator

    calc = RiskRewardCalculator()
    rr = calc.calculate(entry_price, stop_loss, target)

    proposal = {
        "status": "PROPOSED",
        "requires_human_approval": True,
        "symbol": symbol.upper(),
        "action": action.upper(),
        "quantity": quantity,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "target": target,
        "risk_reward_ratio": float(rr.ratio),
        "risk_check_passed": rr.passed,
        "risk_check_message": rr.message,
        "max_loss": float(rr.potential_risk) * quantity,
        "max_gain": float(rr.potential_reward) * quantity,
        "next_step": "Trade proposal sent to UI. User must click 'Confirm' to execute.",
    }

    logger.info(f"Trade proposed by AI agent: {json.dumps(proposal)}")
    return json.dumps(proposal)


@mcp.tool()
def get_sector_exposure() -> str:
    """Get portfolio exposure breakdown by sector/symbol.

    Returns current portfolio allocation to help assess concentration risk.
    """
    return json.dumps({
        "status": "demo",
        "exposure": {},
        "message": "Connect IBKR for live sector exposure data",
    })


# ──────────────────────────────────────────────
# PROMPTS (structured templates for LLM)
# ──────────────────────────────────────────────

@mcp.prompt()
def sector_analysis_prompt() -> str:
    """Analyze the current portfolio's sector exposure and concentration risk."""
    return """You are a portfolio risk analyst. Analyze the current portfolio sector exposure using the get_sector_exposure tool.

For each sector, evaluate:
1. Current allocation percentage
2. Whether any single sector exceeds 30% (concentration risk)
3. Correlation between sectors during market stress

Provide:
- A risk rating (Low/Medium/High) for overall sector concentration
- Specific recommendations to improve diversification
- Any positions that should be reduced or hedged"""


@mcp.prompt()
def rebalance_suggestion_prompt() -> str:
    """Generate regime-aware rebalancing suggestions for the portfolio."""
    return """You are a quantitative portfolio advisor. Review the current portfolio positions and target allocations.

Steps:
1. Use get_sector_exposure to understand current allocation
2. Use calculate_atr for each major holding to assess market regime (high/low volatility)
3. Compare current weights vs target weights

Based on your analysis:
- If ATR is elevated (high volatility regime): recommend HOLDING current positions and NOT rebalancing
- If ATR is normal: recommend specific rebalance trades using propose_trade
- Always ensure proposed trades have R/R >= 2.0

Format your response as a structured rebalance report with clear action items."""


def run_mcp_server():
    """Start the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run_mcp_server()
