"""FastAPI backend — REST endpoints and WebSocket for real-time data."""

from decimal import Decimal

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Portfolio Tracker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---

class OrderPreviewRequest(BaseModel):
    symbol: str
    action: str
    quantity: float
    entry_price: float
    stop_loss_price: float | None = None
    target_price: float
    atr_multiplier: float | None = None


class PortfolioCreateRequest(BaseModel):
    name: str
    description: str = ""
    template: str | None = None
    targets: list[dict] | None = None


class HoldingAddRequest(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float


# --- REST Endpoints ---

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio holdings and PnL (placeholder)."""
    return {
        "net_liquidation_value": 0,
        "available_funds": 0,
        "positions": [],
        "message": "Connect IBKR to see live data",
    }


@app.get("/api/portfolio/templates")
async def get_templates():
    """List available portfolio templates."""
    from portfolio_tracker.orchestrator.portfolio_builder import PortfolioBuilder
    return {"templates": PortfolioBuilder.get_available_templates()}


@app.post("/api/portfolio/create")
async def create_portfolio(req: PortfolioCreateRequest):
    """Create a new target portfolio (from template or custom)."""
    # In production, this would use a real DB session
    return {
        "status": "created",
        "name": req.name,
        "template": req.template,
        "targets": req.targets,
    }


@app.post("/api/portfolio/{portfolio_id}/holdings")
async def add_holding(portfolio_id: str, req: HoldingAddRequest):
    """Add a holding to a portfolio."""
    return {
        "status": "added",
        "portfolio_id": portfolio_id,
        "symbol": req.symbol,
        "quantity": req.quantity,
    }


@app.get("/api/indicators/{symbol}")
async def get_indicators(symbol: str):
    """Get computed technical indicators for a symbol (placeholder)."""
    return {
        "symbol": symbol.upper(),
        "sma_50": None,
        "sma_200": None,
        "ema_12": None,
        "ema_26": None,
        "atr_14": None,
        "vwap": None,
        "message": "Connect IBKR to compute live indicators",
    }


@app.post("/api/orders/preview")
async def preview_order(req: OrderPreviewRequest):
    """Pre-trade risk calculation without execution."""
    from portfolio_tracker.engine.risk_reward import RiskRewardCalculator

    calc = RiskRewardCalculator()
    stop = req.stop_loss_price or (req.entry_price * 0.95)  # Default 5% stop
    rr = calc.calculate(req.entry_price, stop, req.target_price)

    max_loss = float(rr.potential_risk) * req.quantity

    return {
        "symbol": req.symbol.upper(),
        "action": req.action.upper(),
        "quantity": req.quantity,
        "entry_price": req.entry_price,
        "stop_loss_price": float(rr.stop_loss_price),
        "target_price": req.target_price,
        "risk_reward_ratio": float(rr.ratio),
        "max_potential_loss": round(max_loss, 2),
        "risk_check_passed": rr.passed,
        "risk_check_message": rr.message,
    }


@app.post("/api/orders/submit")
async def submit_order(req: OrderPreviewRequest):
    """Submit a validated order (requires IBKR connection)."""
    return {
        "status": "not_connected",
        "message": "IBKR connection required for live order submission",
    }


@app.get("/api/history/trades")
async def get_trade_history():
    """Get execution history (placeholder)."""
    return {"trades": []}


# --- WebSocket for real-time KPIs ---

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass


ws_manager = ConnectionManager()


@app.websocket("/ws/kpi")
async def websocket_kpi(websocket: WebSocket):
    """Real-time KPI updates via WebSocket."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # In production, this streams real IBKR account data
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
