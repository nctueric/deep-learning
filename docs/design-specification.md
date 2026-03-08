# Portfolio Tracker — Design Specification

## Overview

A US stock portfolio management system built on **Interactive Brokers (IBKR) API** with **AI agent** capabilities, integrating automated trading, dynamic risk management, technical indicator computation, and LLM-powered decision support.

---

## 1. System Architecture: Modular Monolith + Lightweight SOA

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| IBKR Communication | ib_async (asyncio-based TWS API wrapper) |
| Frontend | Streamlit + Plotly |
| Database | PostgreSQL (BRIN indexes for OHLCV, JSONB for snapshots) |
| Cache | Redis (latest quotes, session state) |
| Technical Indicators | TA-Lib (C-based, low-latency vectorized computation) |
| AI Integration | FastMCP (Model Context Protocol) + LangGraph |

---

## 2. Data Flow Diagram (DFD)

### Level 0: Context Diagram

Three external entities interact with the system:

1. **IBKR Server** — Market data source & trade execution endpoint (TWS API / CP Web API)
2. **User / Trader** — Web UI for portfolio management, risk preferences, trade approval
3. **LLM API (Claude / OpenAI)** — External AI brain for analysis and trade suggestions via MCP

### Level 1: Core Subsystems

| Process | Name | Responsibility |
|---|---|---|
| 1.0 | Market Data & State Aggregation | IBKR connection, rate limiting (token bucket), real-time streaming, data normalization → PostgreSQL + Redis |
| 2.0 | Quant Analysis & Risk Engine | TA-Lib indicators (SMA/EMA/VWAP/ATR), R/R ratio calculation, dynamic stop-loss, pass/fail gating |
| 3.0 | Decision Orchestration & UI | FastAPI REST + WebSocket, Streamlit dashboard, candidate order assembly |
| 4.0 | Order Execution & Position Tracking | Pre-trade margin check, leverage validation, order submission, execution report handling |

---

## 3. Quantitative Decision Models

### 3.1 Risk/Reward Ratio (R/R) — Mandatory Pre-trade Filter

$$\text{R/R Ratio} = \frac{|\text{Target Price} - \text{Entry Price}|}{|\text{Entry Price} - \text{Stop Loss Price}|}$$

- **System default threshold:** R/R ≥ 2.0
- Orders failing this check are **blocked** at the business logic layer
- Configurable per-user via `config/settings.py`

### 3.2 ATR-Based Dynamic Stop-Loss

True Range:

$$TR_t = \max[(H_t - L_t),\ |H_t - C_{t-1}|,\ |L_t - C_{t-1}|]$$

Average True Range (default n=14):

$$ATR_n = \frac{1}{n} \sum_{i=1}^{n} TR_{t-i+1}$$

Stop Price for long positions:

$$\text{Stop Price} = \text{Entry Price} - (M \times ATR_n)$$

- Multiplier **M** range: [1.5, 3.0] (user-configurable)
- High volatility → wider stop (avoid noise whipsaw)
- Low volatility → tighter stop (protect unrealized gains)

### 3.3 Technical Indicators (via TA-Lib)

| Indicator | Parameters | Purpose |
|---|---|---|
| SMA | 50, 200 | Long-term trend & bull/bear boundary |
| EMA | 12, 26 | Short-term momentum crossover signals |
| VWAP | Intraday | Institutional fair value, slippage assessment |
| ATR | 14 | Volatility measurement for dynamic stop-loss |

---

## 4. Database Schema (PostgreSQL)

### 4.1 Core Tables

| Table | Purpose | Key Design Decision |
|---|---|---|
| `instruments` | Static reference data for tradeable assets | PK: symbol |
| `historical_ohlcv` | Time-series price data | **BRIN index** on timestamp (not B-Tree) for range query performance |
| `orders` | System-generated order records with risk check results | Includes `risk_reward_ratio`, `status` fields |
| `executions` | IBKR execution reports (fill confirmations) | FK to orders |
| `portfolio_snapshots` | Daily account state + position snapshots | **JSONB** `positions_data` field to avoid expensive JOINs |
| `target_portfolios` | User-defined target allocation models | **JSONB** `targets` field: `[{"symbol": "AAPL", "weight": 0.25}, ...]` |
| `user_portfolios` | Actual holdings per portfolio | FK to instruments and target_portfolios |

### 4.2 Design Rationale

- **BRIN index** on `historical_ohlcv.timestamp`: Data is written chronologically → strong correlation between time and disk block location → BRIN provides exponential query speedup with minimal storage
- **JSONB** for snapshots: Avoids N×M junction tables for daily position records, enables efficient equity curve rendering

---

## 5. Frontend UI (Streamlit + Plotly)

### 5.1 Portfolio Builder (Primary User Entry Point)

| Page | Function |
|---|---|
| `builder.py` | Portfolio construction wizard — ticker search, add/edit/remove holdings, set target weights |
| `import_sync.py` | One-click IBKR account import & sync |
| `allocation.py` | Visual weight editor — sliders per symbol/sector, live pie chart |
| `rebalance.py` | Current vs. target weights comparison, generate rebalance orders |

### 5.2 Dashboard & Trading Terminal

| Component | Details |
|---|---|
| KPI Cards | NLV, Daily PnL, Unrealized PnL, Available Margin — real-time via WebSocket, green/red color coding |
| Allocation Module | Plotly sunburst chart (sector → asset class → symbol), target vs. actual bar chart |
| Trading Terminal | Candlestick chart with MA/VWAP overlays, risk-aware order form (auto-disables if R/R < threshold) |
| AI Copilot | Chat window connected to LLM via MCP, natural language portfolio queries |

---

## 6. Backtesting Engine (Event-Driven)

- **NOT vectorized** — avoids look-ahead bias
- Shares same `engine/` code as live trading (per nautilus_trader philosophy)
- Components:
  - Data Replay Simulator (historical OHLCV → simulated tick stream)
  - Virtual Matching Engine (slippage penalties + IBKR commission model)
  - Walk-Forward Optimization (in-sample / out-of-sample splits)
- Output metrics: Sharpe Ratio, Maximum Drawdown, Win Rate, PnL distribution

---

## 7. AI Agent Integration (MCP)

### 7.1 IBKR-MCP-Server (FastMCP)

| Primitive | Examples |
|---|---|
| **Resources** (read-only) | `ibkr://portfolio/positions`, `ohlcv://NVDA/1D`, `ibkr://account/summary` |
| **Tools** (executable) | `calculate_atr()`, `analyze_risk_reward()`, `propose_trade()`, `get_sector_exposure()` |
| **Prompts** (templates) | Sector exposure analysis, regime-aware rebalancing suggestions |

### 7.2 Safety Architecture

- `propose_trade()` generates `CandidateOrder` only — **never direct execution**
- All candidates pass through risk engine (margin check + R/R validation)
- **Human-in-the-loop**: order appears in UI, user must click confirm

### 7.3 Multi-Agent Workflow (LangGraph)

1. **Data Agent** — Scans IBKR data streams, collects features
2. **Quant Agent** — Runs TA-Lib indicators, flags stop-loss proximity
3. **Orchestrator Agent** — Synthesizes analysis, generates rebalance recommendations

---

## 8. Reference Projects

| Project | Stack | Contribution |
|---|---|---|
| ib_async / ib_insync | Python, asyncio | Async TWS API wrapper, event loop management |
| thetagang | Python, TWS API | Regime-aware rebalancing, VIX hedging |
| ib_strategy_project | Python, TWS API | Atomic margin checks, 0.3x leverage steps, 5-layer timeout protection |
| nautilus_trader | Rust, Python | Backtest = live code, zero look-ahead bias |
