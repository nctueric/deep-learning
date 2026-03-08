# Portfolio Tracker — Development Plan

## Phase 0: Project Foundation & Infrastructure

**Goal:** Runnable project skeleton with DB schema and all dependencies resolved.

- [ ] Initialize Python project with `pyproject.toml`
- [ ] Establish modular monolith directory structure
- [ ] Create global config (`config/settings.py`) with risk thresholds
- [ ] Set up `docker-compose.yml` for PostgreSQL + Redis
- [ ] Write Alembic migration scripts for all core tables
- [ ] Set up `.env.example` for environment variables

```
portfolio_tracker/
├── config/              # Global settings, risk thresholds
├── core/
│   ├── models/          # SQLAlchemy ORM definitions
│   └── schemas/         # Pydantic request/response models
├── gateway/             # Process 1.0 — IBKR connection & rate limiter
├── engine/              # Process 2.0 — TA-Lib, ATR, R/R calculator
├── orchestrator/        # Process 3.0 — FastAPI routes, WebSocket
├── executor/            # Process 4.0 — Order validation & execution
├── backtest/            # Event-driven backtesting engine
├── mcp_server/          # IBKR-MCP-Server (FastMCP)
├── ui/                  # Streamlit pages
└── tests/
```

---

## Phase 1: Market Data Gateway (DFD Process 1.0)

**Goal:** Connect to IBKR paper trading, stream live data, persist to DB.

- [ ] `gateway/ibkr_client.py` — async connection manager (ib_async), auto-reconnect
- [ ] `gateway/rate_limiter.py` — Token Bucket (50 req/s global, 60 hist req/10min)
- [ ] `gateway/data_streamer.py` — Real-time tick subscription, OHLCV normalization → PostgreSQL (BRIN index) + Redis cache
- [ ] `gateway/account_sync.py` — Periodic portfolio snapshot → `portfolio_snapshots` (JSONB)

---

## Phase 2: Quantitative Analysis Engine (DFD Process 2.0)

**Goal:** Standalone engine that outputs indicators, suggested stop-loss, R/R ratio, and pass/fail gate.

- [ ] `engine/indicators.py` — TA-Lib wrapper: SMA(50,200), EMA(12,26), VWAP, ATR(14)
- [ ] `engine/risk_reward.py` — R/R calculation with configurable threshold (default ≥ 2.0)
- [ ] `engine/dynamic_stop.py` — ATR-based stop-loss: `Stop = Entry - (M × ATR_14)`, M ∈ [1.5, 3.0]
- [ ] `engine/candidate_order.py` — Combines R/R check + ATR stop → `CandidateOrder` with metadata

---

## Phase 3: Order Execution & Position Tracking (DFD Process 4.0)

**Goal:** Full order lifecycle: validate → submit → monitor → confirm → persist.

- [ ] `executor/margin_checker.py` — Pre-trade margin check via IBKR `whatIfOrder`, leverage cap (0.3x steps, 3x emergency)
- [ ] `executor/order_manager.py` — CandidateOrder → IBKR Order, trailing stop attachment, execution report handling
- [ ] `executor/position_tracker.py` — Real-time position sync, available funds tracking
- [ ] 5-layer timeout protection (anti-stuck mechanism)

---

## Phase 4: Portfolio Builder UI ⭐

**Goal:** Users can create, import, edit, and visualize their stock portfolio.

This is the **primary user entry point** — before charting, backtesting, or AI features.

### User Flows
1. **Add Holdings** — Ticker search (IBKR contract autocomplete), input shares & cost basis
2. **Manual Construction** — Set target % weights per symbol, system calculates required shares
3. **Import from Broker** — One-click sync of all current IBKR positions
4. **Edit / Remove** — Adjust quantities, update cost basis, delete positions
5. **Portfolio Templates** — Presets: "60/40", "Tech Heavy", "Dividend Income"

### UI Pages
- [ ] `ui/pages/builder.py` — Portfolio construction wizard
- [ ] `ui/pages/import_sync.py` — IBKR account import & sync
- [ ] `ui/pages/allocation.py` — Visual weight editor (sliders + live pie chart)
- [ ] `ui/pages/rebalance.py` — Current vs. target weights, one-click rebalance order generation

### Backend
- [ ] `orchestrator/portfolio_builder.py` — CRUD for user-defined portfolios
- [ ] `core/models/target_portfolio.py` — DB tables: `target_portfolios`, `user_portfolios`
- [ ] `orchestrator/rebalance_engine.py` — Actual vs. target weight comparison → CandidateOrder list

---

## Phase 5: Dashboard & Trading Terminal (DFD Process 3.0)

**Goal:** Fully functional web UI with real-time data, charting, and risk-aware trading.

### FastAPI Backend
- [ ] `orchestrator/api.py` — REST: `/portfolio`, `/indicators/{symbol}`, `/orders/preview`, `/orders/submit`, `/history/trades`
- [ ] `orchestrator/ws.py` — WebSocket: real-time KPIs at 1s interval

### Streamlit Frontend
- [ ] `ui/pages/dashboard.py` — KPI cards (NLV, PnL, margin) with green/red color coding
- [ ] `ui/pages/portfolio.py` — Plotly sunburst chart, target vs. actual weight comparison
- [ ] `ui/pages/trading.py` — Candlestick chart + MA/VWAP overlays, risk-aware order form (disabled if R/R < 2.0)
- [ ] `ui/pages/history.py` — Transaction log + equity curve
- [ ] `ui/components/ai_chat.py` — AI Copilot placeholder (wired in Phase 7)

---

## Phase 6: Backtesting Engine (parallel with Phase 7)

**Goal:** Prove system edge via historical simulation.

- [ ] `backtest/data_replay.py` — historical_ohlcv → simulated tick stream with internal clock
- [ ] `backtest/virtual_exchange.py` — Matching engine with slippage + IBKR commission model
- [ ] `backtest/runner.py` — Reuses `engine/` code (no look-ahead bias), walk-forward optimization
- [ ] `backtest/report.py` — Sharpe Ratio, Max Drawdown, Win Rate, PnL distribution

---

## Phase 7: MCP AI Agent Integration (parallel with Phase 6)

**Goal:** AI can read portfolio context and propose (never execute) trades.

- [ ] `mcp_server/server.py` — FastMCP server with Resources, Tools, Prompts
- [ ] Safety layer: `propose_trade()` → CandidateOrder only, human-in-the-loop confirmation
- [ ] Wire `ai_chat.py` to Claude API via MCP client
- [ ] (Optional) Multi-agent pipeline: Data Agent → Quant Agent → Orchestrator Agent

---

## Execution Order

```
Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phase 5 ──┬──→ Phase 6
                                                                        └──→ Phase 7
```

- Phases 6 & 7 run in parallel after Phase 5
- Each phase ends with tests + integration verification
- Paper trading validation after Phase 5, before real account connection
