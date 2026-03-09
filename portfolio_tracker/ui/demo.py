"""Portfolio Tracker — Demo Application

A self-contained demo with pre-loaded sample data showcasing all features:
- Dashboard with KPI cards
- Portfolio Builder with templates
- Interactive Trading Terminal with risk-aware order form
- Allocation visualization (pie + bar charts)
- Rebalance analysis
- Backtesting engine with equity curve
- AI Copilot chat interface
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal

st.set_page_config(
    page_title="Portfolio Tracker",
    page_icon="\U0001F4CA",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SAMPLE DATA
# ─────────────────────────────────────────────

DEMO_PORTFOLIO = [
    {"symbol": "AAPL", "shares": 150, "avg_cost": 165.20, "current_price": 227.48, "sector": "Technology"},
    {"symbol": "MSFT", "shares": 80, "avg_cost": 310.50, "current_price": 414.20, "sector": "Technology"},
    {"symbol": "NVDA", "shares": 200, "avg_cost": 48.30, "current_price": 131.29, "sector": "Technology"},
    {"symbol": "GOOGL", "shares": 60, "avg_cost": 120.80, "current_price": 171.85, "sector": "Communication"},
    {"symbol": "AMZN", "shares": 45, "avg_cost": 135.60, "current_price": 205.74, "sector": "Consumer"},
    {"symbol": "JPM", "shares": 100, "avg_cost": 148.90, "current_price": 253.95, "sector": "Financial"},
    {"symbol": "JNJ", "shares": 70, "avg_cost": 162.30, "current_price": 157.18, "sector": "Healthcare"},
    {"symbol": "VTI", "shares": 120, "avg_cost": 210.40, "current_price": 282.55, "sector": "ETF"},
    {"symbol": "BND", "shares": 200, "avg_cost": 73.50, "current_price": 71.23, "sector": "Fixed Income"},
]

PORTFOLIO_TEMPLATES = {
    "60/40 Stocks/Bonds": [
        {"symbol": "VTI", "weight": 0.42}, {"symbol": "VXUS", "weight": 0.18},
        {"symbol": "BND", "weight": 0.28}, {"symbol": "BNDX", "weight": 0.12},
    ],
    "Tech Heavy": [
        {"symbol": "QQQ", "weight": 0.30}, {"symbol": "AAPL", "weight": 0.15},
        {"symbol": "MSFT", "weight": 0.15}, {"symbol": "NVDA", "weight": 0.10},
        {"symbol": "GOOGL", "weight": 0.10}, {"symbol": "AMZN", "weight": 0.10},
        {"symbol": "META", "weight": 0.10},
    ],
    "Dividend Income": [
        {"symbol": "VYM", "weight": 0.25}, {"symbol": "SCHD", "weight": 0.25},
        {"symbol": "JNJ", "weight": 0.10}, {"symbol": "PG", "weight": 0.10},
        {"symbol": "KO", "weight": 0.10}, {"symbol": "PEP", "weight": 0.10},
        {"symbol": "O", "weight": 0.10},
    ],
    "S&P 500 Core": [
        {"symbol": "SPY", "weight": 0.50}, {"symbol": "VOO", "weight": 0.50},
    ],
}


def _compute_portfolio_df():
    rows = []
    for p in DEMO_PORTFOLIO:
        market_value = p["shares"] * p["current_price"]
        cost_basis = p["shares"] * p["avg_cost"]
        unrealized_pnl = market_value - cost_basis
        pnl_pct = (unrealized_pnl / cost_basis) * 100
        rows.append({
            "Symbol": p["symbol"],
            "Sector": p["sector"],
            "Shares": p["shares"],
            "Avg Cost": p["avg_cost"],
            "Price": p["current_price"],
            "Market Value": round(market_value, 2),
            "Cost Basis": round(cost_basis, 2),
            "Unrealized P&L": round(unrealized_pnl, 2),
            "P&L %": round(pnl_pct, 1),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

st.sidebar.title("\U0001F4CA Portfolio Tracker")
st.sidebar.caption("IBKR + AI Agent | Demo Mode")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "\U0001F3E0 Dashboard",
        "\U0001F3D7 Portfolio Builder",
        "\U0001F4CA Allocation",
        "\U0001F4C8 Trading Terminal",
        "\u2696 Rebalance",
        "\U0001F4DC Trade History",
        "\U0001F9EA Backtest",
        "\U0001F916 AI Copilot",
    ],
)

st.sidebar.divider()
st.sidebar.success("IBKR Paper Trading: Connected")
st.sidebar.info(f"Last sync: {datetime.now().strftime('%H:%M:%S')}")

# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────

if page == "\U0001F3E0 Dashboard":
    st.title("\U0001F3E0 Portfolio Dashboard")

    df = _compute_portfolio_df()
    nlv = df["Market Value"].sum()
    cost = df["Cost Basis"].sum()
    total_pnl = df["Unrealized P&L"].sum()
    daily_pnl = nlv * 0.0082  # Simulated +0.82% today

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Net Liquidation Value", f"${nlv:,.2f}")
    with col2:
        st.metric("Daily P&L", f"${daily_pnl:,.2f}", delta=f"+{daily_pnl / nlv * 100:.2f}%")
    with col3:
        st.metric("Unrealized P&L", f"${total_pnl:,.2f}", delta=f"+{total_pnl / cost * 100:.1f}%")
    with col4:
        margin_available = nlv * 0.65
        st.metric("Available Margin", f"${margin_available:,.2f}")

    st.divider()

    # Positions table
    col_table, col_chart = st.columns([3, 2])
    with col_table:
        st.subheader("Current Positions")
        styled_df = df[["Symbol", "Shares", "Price", "Market Value", "Unrealized P&L", "P&L %"]].copy()
        st.dataframe(
            styled_df.style.applymap(
                lambda v: "color: #22c55e" if isinstance(v, (int, float)) and v > 0
                else "color: #ef4444" if isinstance(v, (int, float)) and v < 0
                else "",
                subset=["Unrealized P&L", "P&L %"],
            ),
            use_container_width=True,
            height=370,
        )

    with col_chart:
        st.subheader("Sector Allocation")
        sector_data = df.groupby("Sector")["Market Value"].sum().reset_index()
        fig = px.pie(
            sector_data, values="Market Value", names="Sector",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textposition="inside", textinfo="label+percent")
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Mini equity curve
    st.subheader("Portfolio Performance (1Y)")
    np.random.seed(42)
    days = 252
    returns = np.random.randn(days) * 0.012 + 0.0004
    equity = cost * np.cumprod(1 + returns)
    dates = pd.date_range(end=datetime.now(), periods=days, freq="B")

    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(
        x=dates, y=equity, mode="lines", name="Portfolio",
        line=dict(color="#3b82f6", width=2),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
    ))
    fig_eq.add_hline(y=cost, line_dash="dash", line_color="gray", annotation_text="Cost Basis")
    fig_eq.update_layout(
        xaxis_title="", yaxis_title="Portfolio Value ($)",
        height=280, margin=dict(t=10, b=30),
        yaxis_tickformat="$,.0f",
    )
    st.plotly_chart(fig_eq, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE: PORTFOLIO BUILDER
# ─────────────────────────────────────────────

elif page == "\U0001F3D7 Portfolio Builder":
    st.title("\U0001F3D7 Portfolio Builder")

    tab1, tab2, tab3 = st.tabs(["From Template", "Build Custom", "Import from IBKR"])

    with tab1:
        st.subheader("Start from a Template")
        template_name = st.selectbox("Choose a template", list(PORTFOLIO_TEMPLATES.keys()))
        targets = PORTFOLIO_TEMPLATES[template_name]

        cols = st.columns(min(len(targets), 4))
        for i, t in enumerate(targets):
            with cols[i % 4]:
                st.metric(t["symbol"], f"{t['weight'] * 100:.0f}%")

        total_w = sum(t["weight"] for t in targets)
        st.progress(total_w, text=f"Total allocation: {total_w * 100:.0f}%")

        custom_name = st.text_input("Portfolio name", value=template_name)
        if st.button("Create Portfolio", type="primary"):
            st.success(f"Portfolio '{custom_name}' created with {len(targets)} holdings!")
            st.balloons()

    with tab2:
        st.subheader("Build a Custom Portfolio")
        if "custom_targets" not in st.session_state:
            st.session_state.custom_targets = [
                {"symbol": "AAPL", "weight": 0.25},
                {"symbol": "MSFT", "weight": 0.20},
                {"symbol": "NVDA", "weight": 0.15},
            ]

        col_add1, col_add2, col_add3 = st.columns([2, 1, 1])
        with col_add1:
            new_sym = st.text_input("Ticker", placeholder="GOOGL").upper()
        with col_add2:
            new_w = st.number_input("Weight (%)", 0.0, 100.0, 10.0, 1.0)
        with col_add3:
            st.write("")
            st.write("")
            if st.button("Add") and new_sym:
                st.session_state.custom_targets.append({"symbol": new_sym, "weight": new_w / 100})
                st.rerun()

        total = sum(t["weight"] for t in st.session_state.custom_targets)
        for t in st.session_state.custom_targets:
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{t['symbol']}**")
            c2.write(f"{t['weight'] * 100:.0f}%")

        color = "normal" if abs(total - 1.0) <= 0.01 else "off"
        st.progress(min(total, 1.0), text=f"Total: {total * 100:.0f}%")

    with tab3:
        st.subheader("Import from Interactive Brokers")
        st.success("Connected to IBKR Paper Trading (port 7497)")
        if st.button("Sync Positions", type="primary"):
            with st.spinner("Importing positions from IBKR..."):
                import time; time.sleep(1)
            st.success(f"Imported {len(DEMO_PORTFOLIO)} positions successfully!")
            st.dataframe(
                _compute_portfolio_df()[["Symbol", "Shares", "Avg Cost", "Market Value"]],
                use_container_width=True,
            )


# ─────────────────────────────────────────────
# PAGE: ALLOCATION
# ─────────────────────────────────────────────

elif page == "\U0001F4CA Allocation":
    st.title("\U0001F4CA Portfolio Allocation")

    df = _compute_portfolio_df()
    total_val = df["Market Value"].sum()
    df["Weight %"] = (df["Market Value"] / total_val * 100).round(1)

    col_pie, col_sunburst = st.columns(2)

    with col_pie:
        st.subheader("By Symbol")
        fig = px.pie(
            df, values="Market Value", names="Symbol",
            color_discrete_sequence=px.colors.qualitative.Plotly,
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="label+percent")
        fig.update_layout(height=400, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_sunburst:
        st.subheader("By Sector > Symbol")
        fig_sun = px.sunburst(
            df, path=["Sector", "Symbol"], values="Market Value",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_sun.update_layout(height=400, margin=dict(t=10, b=10))
        st.plotly_chart(fig_sun, use_container_width=True)

    # Weight sliders
    st.divider()
    st.subheader("Adjust Target Weights")
    cols = st.columns(3)
    for i, row in df.iterrows():
        with cols[i % 3]:
            st.slider(
                f"{row['Symbol']}",
                0.0, 40.0,
                float(row["Weight %"]),
                0.5,
                key=f"w_{row['Symbol']}",
            )


# ─────────────────────────────────────────────
# PAGE: TRADING TERMINAL
# ─────────────────────────────────────────────

elif page == "\U0001F4C8 Trading Terminal":
    st.title("\U0001F4C8 Trading Terminal")

    from portfolio_tracker.engine.indicators import TechnicalIndicators
    from portfolio_tracker.engine.risk_reward import RiskRewardCalculator
    from portfolio_tracker.engine.dynamic_stop import DynamicStopCalculator

    col_chart, col_order = st.columns([2, 1])

    with col_chart:
        symbol = st.text_input("Symbol", value="NVDA").upper()

        # Generate realistic candlestick data
        np.random.seed(hash(symbol) % 2**31)
        n = 120
        base = {"NVDA": 131, "AAPL": 227, "MSFT": 414, "GOOGL": 172, "AMZN": 206}.get(symbol, 150)
        close = base + np.cumsum(np.random.randn(n) * 1.5)
        close = np.maximum(close, base * 0.7)
        high = close + np.abs(np.random.randn(n)) * 2.5
        low = close - np.abs(np.random.randn(n)) * 2.5
        open_p = close + np.random.randn(n) * 1.2
        dates = pd.date_range(end=datetime.now(), periods=n, freq="B")

        # Compute indicators
        indicators = TechnicalIndicators()
        result = indicators.compute_all(symbol, high, low, close)

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=dates, open=open_p, high=high, low=low, close=close,
            name=symbol, increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
        ))
        if result.sma_50 is not None:
            fig.add_trace(go.Scatter(x=dates, y=result.sma_50, name="SMA 50", line=dict(color="#f59e0b", width=1.5)))
        if result.ema_12 is not None:
            fig.add_trace(go.Scatter(x=dates, y=result.ema_12, name="EMA 12", line=dict(color="#8b5cf6", width=1, dash="dot")))

        fig.update_layout(
            title=f"{symbol} \u2014 Daily", xaxis_rangeslider_visible=False,
            height=480, margin=dict(t=35, b=20),
            yaxis_title="Price ($)", xaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Indicator cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SMA 50", f"${result.latest_sma_50:.2f}" if result.latest_sma_50 else "N/A")
        c2.metric("SMA 200", f"${result.latest_sma_200:.2f}" if result.latest_sma_200 else "N/A")
        c3.metric("EMA 12", f"${result.latest_ema_12:.2f}" if result.latest_ema_12 else "N/A")
        c4.metric("ATR 14", f"${result.latest_atr:.2f}" if result.latest_atr else "N/A")

    # Risk-aware order form
    with col_order:
        st.subheader("Place Order")
        action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
        quantity = st.number_input("Shares", 1, 10000, 50)
        entry = st.number_input("Entry Price", 0.01, 9999.0, float(close[-1]), 0.01)
        target = st.number_input("Target Price", 0.01, 9999.0, round(float(entry * 1.12), 2), 0.01)

        use_atr = st.checkbox("Use ATR Dynamic Stop", value=True)
        if use_atr:
            atr_mult = st.slider("ATR Multiplier", 1.5, 3.0, 2.0, 0.1)
            if result.latest_atr:
                stop_calc = DynamicStopCalculator()
                stop_r = stop_calc.calculate_from_atr(symbol, entry, result.latest_atr, atr_mult)
                stop = float(stop_r.stop_price)
                st.info(f"ATR Stop: **${stop:.2f}** ({stop_r.stop_pct}% below entry)")
            else:
                stop = round(entry * 0.95, 2)
        else:
            stop = st.number_input("Stop Loss", 0.01, 9999.0, round(float(entry * 0.95), 2), 0.01)

        # R/R calculation
        rr_calc = RiskRewardCalculator()
        rr = rr_calc.calculate(entry, stop, target)

        st.divider()
        st.write("**Risk Analysis**")

        risk_col, reward_col = st.columns(2)
        with risk_col:
            st.metric("Max Loss", f"${float(rr.potential_risk) * quantity:,.2f}")
        with reward_col:
            st.metric("Max Gain", f"${float(rr.potential_reward) * quantity:,.2f}")

        rr_val = float(rr.ratio)
        if rr.passed:
            st.success(f"R/R Ratio: **{rr_val:.2f}** \u2265 2.0 \u2014 Trade allowed")
            if st.button("Submit Order", type="primary", use_container_width=True):
                st.success(f"{action} {quantity} shares of {symbol} @ ${entry:.2f}")
                st.caption(f"Stop: ${stop:.2f} | Target: ${target:.2f}")
        else:
            st.error(f"R/R Ratio: **{rr_val:.2f}** < 2.0 \u2014 Trade BLOCKED")
            st.button("Submit Order", type="primary", disabled=True, use_container_width=True)
            st.caption("Adjust stop/target to achieve R/R \u2265 2.0")


# ─────────────────────────────────────────────
# PAGE: REBALANCE
# ─────────────────────────────────────────────

elif page == "\u2696 Rebalance":
    st.title("\u2696 Rebalance Analysis")

    df = _compute_portfolio_df()
    total_val = df["Market Value"].sum()

    # Simulated target weights
    target_map = {
        "AAPL": 0.15, "MSFT": 0.15, "NVDA": 0.12, "GOOGL": 0.08,
        "AMZN": 0.08, "JPM": 0.10, "JNJ": 0.07, "VTI": 0.15, "BND": 0.10,
    }

    rebalance_data = []
    for _, row in df.iterrows():
        current_w = row["Market Value"] / total_val
        target_w = target_map.get(row["Symbol"], 0.10)
        drift = (current_w - target_w) * 100
        action = "SELL" if drift > 1.0 else ("BUY" if drift < -1.0 else "HOLD")
        rebalance_data.append({
            "Symbol": row["Symbol"],
            "Current %": round(current_w * 100, 1),
            "Target %": round(target_w * 100, 1),
            "Drift %": round(drift, 1),
            "Action": action,
        })

    reb_df = pd.DataFrame(rebalance_data)

    # Grouped bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Target", x=reb_df["Symbol"], y=reb_df["Target %"], marker_color="#3b82f6"))
    fig.add_trace(go.Bar(name="Current", x=reb_df["Symbol"], y=reb_df["Current %"], marker_color="#f97316"))
    fig.update_layout(barmode="group", title="Target vs Current Allocation", yaxis_title="Weight (%)", height=380)
    st.plotly_chart(fig, use_container_width=True)

    # Actions table
    actions = reb_df[reb_df["Action"] != "HOLD"]
    if actions.empty:
        st.success("Portfolio is within tolerance. No rebalancing needed.")
    else:
        st.subheader("Required Actions")
        st.dataframe(
            actions.style.applymap(
                lambda v: "color: #22c55e" if v == "BUY" else "color: #ef4444" if v == "SELL" else "",
                subset=["Action"],
            ),
            use_container_width=True,
        )
        tolerance = st.slider("Drift Tolerance (%)", 0.5, 5.0, 1.0, 0.5)
        if st.button("Generate Rebalance Orders", type="primary"):
            st.success(f"{len(actions)} candidate orders generated (pending R/R validation)")


# ─────────────────────────────────────────────
# PAGE: TRADE HISTORY
# ─────────────────────────────────────────────

elif page == "\U0001F4DC Trade History":
    st.title("\U0001F4DC Trade History")

    tab_log, tab_equity = st.tabs(["Execution Log", "Equity Curve"])

    with tab_log:
        trades = pd.DataFrame([
            {"Date": "2025-11-15", "Symbol": "NVDA", "Action": "BUY", "Qty": 100, "Price": 48.30, "R/R": 3.2, "P&L": "+$8,299", "Status": "FILLED"},
            {"Date": "2025-12-02", "Symbol": "AAPL", "Action": "BUY", "Qty": 150, "Price": 165.20, "R/R": 2.8, "P&L": "+$9,342", "Status": "FILLED"},
            {"Date": "2026-01-10", "Symbol": "MSFT", "Action": "BUY", "Qty": 80, "Price": 310.50, "R/R": 2.5, "P&L": "+$8,296", "Status": "FILLED"},
            {"Date": "2026-01-18", "Symbol": "GOOGL", "Action": "BUY", "Qty": 60, "Price": 120.80, "R/R": 2.1, "P&L": "+$3,063", "Status": "FILLED"},
            {"Date": "2026-02-05", "Symbol": "JPM", "Action": "BUY", "Qty": 100, "Price": 148.90, "R/R": 2.4, "P&L": "+$10,505", "Status": "FILLED"},
            {"Date": "2026-02-14", "Symbol": "TSLA", "Action": "BUY", "Qty": 30, "Price": 380.00, "R/R": 1.8, "P&L": "", "Status": "BLOCKED (R/R < 2.0)"},
            {"Date": "2026-02-20", "Symbol": "AMZN", "Action": "BUY", "Qty": 45, "Price": 135.60, "R/R": 2.6, "P&L": "+$3,156", "Status": "FILLED"},
            {"Date": "2026-03-01", "Symbol": "VTI", "Action": "BUY", "Qty": 120, "Price": 210.40, "R/R": 2.3, "P&L": "+$8,658", "Status": "FILLED"},
        ])
        st.dataframe(
            trades.style.applymap(
                lambda v: "color: #ef4444; font-weight: bold" if "BLOCKED" in str(v) else "",
                subset=["Status"],
            ),
            use_container_width=True,
            height=340,
        )
        st.caption("Note: TSLA order was automatically blocked by the risk engine (R/R 1.8 < 2.0)")

    with tab_equity:
        np.random.seed(123)
        days = 252
        returns = np.random.randn(days) * 0.011 + 0.0004
        equity = 200000 * np.cumprod(1 + returns)
        dates = pd.date_range(end=datetime.now(), periods=days, freq="B")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=equity, mode="lines", name="Portfolio",
            line=dict(color="#3b82f6", width=2),
            fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
        ))
        fig.add_hline(y=200000, line_dash="dash", line_color="gray", annotation_text="Starting Capital")
        fig.update_layout(title="Portfolio Equity Curve", height=400, yaxis_tickformat="$,.0f")
        st.plotly_chart(fig, use_container_width=True)

        c1, c2, c3, c4 = st.columns(4)
        total_ret = (equity[-1] / equity[0] - 1) * 100
        max_dd = np.min(equity / np.maximum.accumulate(equity) - 1) * 100
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
        c1.metric("Total Return", f"+{total_ret:.1f}%")
        c2.metric("Max Drawdown", f"{max_dd:.1f}%")
        c3.metric("Sharpe Ratio", f"{sharpe:.2f}")
        c4.metric("Win Rate", "87.5%")


# ─────────────────────────────────────────────
# PAGE: BACKTEST
# ─────────────────────────────────────────────

elif page == "\U0001F9EA Backtest":
    st.title("\U0001F9EA Strategy Backtesting")

    from portfolio_tracker.backtest.data_replay import DataReplaySimulator
    from portfolio_tracker.backtest.virtual_exchange import VirtualExchange
    from portfolio_tracker.backtest.runner import BacktestRunner, BacktestConfig
    from portfolio_tracker.backtest.data_replay import MarketEvent
    from portfolio_tracker.engine.indicators import TechnicalIndicators

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        bt_symbol = st.text_input("Symbol", value="AAPL", key="bt_sym")
        initial_cash = st.number_input("Initial Capital ($)", 10000, 1000000, 100000, 10000)
        bt_days = st.slider("Period (trading days)", 60, 500, 252)
    with col_cfg2:
        rr_thresh = st.number_input("Min R/R Ratio", 1.0, 5.0, 2.0, 0.1)
        atr_m = st.slider("ATR Multiplier", 1.5, 3.0, 2.0, 0.1, key="bt_atr")
        slippage_bps = st.number_input("Slippage (bps)", 0.0, 50.0, 5.0, 1.0)

    if st.button("Run Backtest", type="primary"):
        with st.spinner("Running event-driven backtest..."):
            np.random.seed(42)
            close = np.cumsum(np.random.randn(bt_days) * 2) + 180
            close = np.maximum(close, 50)
            high = close + np.abs(np.random.randn(bt_days)) * 3
            low = close - np.abs(np.random.randn(bt_days)) * 3
            low = np.maximum(low, 10)
            open_p = close + np.random.randn(bt_days) * 1
            volume = np.random.randint(1_000_000, 50_000_000, bt_days)
            timestamps = [datetime(2024, 1, 2) + timedelta(days=i) for i in range(bt_days)]

            sim = DataReplaySimulator(symbols=[bt_symbol])
            sim.load_from_arrays(bt_symbol, timestamps, open_p, high, low, close, volume)

            def sma_crossover_strategy(event, history, exchange, indicators):
                closes = history.get(event.symbol, [])
                if len(closes) < 50:
                    return
                arr = np.array(closes)
                sma12 = np.mean(arr[-12:])
                sma50 = np.mean(arr[-50:])
                pos = exchange.positions.get(event.symbol)
                has_pos = pos is not None and pos.quantity > 0
                if not has_pos and sma12 > sma50:
                    qty = int(exchange.cash * 0.15 / event.close)
                    if qty > 0:
                        exchange.submit_order(event.symbol, "BUY", qty)
                elif has_pos and sma12 < sma50:
                    exchange.submit_order(event.symbol, "SELL", pos.quantity)

            config = BacktestConfig(
                initial_cash=initial_cash, slippage_bps=slippage_bps,
                risk_reward_threshold=rr_thresh, atr_multiplier=atr_m,
            )
            runner = BacktestRunner(config)
            report = runner.run(sim, sma_crossover_strategy)

        st.subheader("Results")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Return", f"{report.total_return_pct:+.1f}%")
        c2.metric("Sharpe Ratio", f"{report.sharpe_ratio:.2f}")
        c3.metric("Max Drawdown", f"{report.max_drawdown_pct:.1f}%")
        c4.metric("Win Rate", f"{report.win_rate_pct:.0f}%")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Total Trades", report.total_trades)
        c6.metric("Profit Factor", f"{report.profit_factor:.2f}" if report.profit_factor < 999 else "\u221E")
        c7.metric("Commission", f"${report.total_commission:,.2f}")
        c8.metric("Final Equity", f"${report.final_equity:,.2f}")

        if report.equity_curve:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=report.timestamps, y=report.equity_curve,
                mode="lines", name="Equity",
                line=dict(color="#3b82f6", width=2),
                fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
            ))
            fig.add_hline(y=initial_cash, line_dash="dash", line_color="gray", annotation_text="Starting Capital")
            fig.update_layout(
                title="Backtest Equity Curve", height=400,
                yaxis_title="Portfolio Value ($)", yaxis_tickformat="$,.0f",
            )
            st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE: AI COPILOT
# ─────────────────────────────────────────────

elif page == "\U0001F916 AI Copilot":
    st.title("\U0001F916 AI Copilot")

    st.info(
        "Chat with your AI portfolio advisor via **Model Context Protocol (MCP)**. "
        "The AI can read portfolio data, compute indicators, and propose trades for your review."
    )

    # MCP tools reference
    with st.expander("Available MCP Tools"):
        st.markdown("""
| Primitive | Name | Description |
|---|---|---|
| **Resource** | `ibkr://portfolio/positions` | Read current positions |
| **Resource** | `ibkr://account/summary` | Read account summary |
| **Resource** | `ohlcv://{symbol}/{timeframe}` | Read historical OHLCV |
| **Tool** | `calculate_atr()` | Compute ATR for volatility |
| **Tool** | `analyze_risk_reward()` | Check R/R ratio |
| **Tool** | `propose_trade()` | Propose trade (human approval required) |
| **Tool** | `get_sector_exposure()` | Portfolio sector breakdown |
| **Prompt** | Sector Analysis | Concentration risk report |
| **Prompt** | Rebalance Suggestion | Regime-aware rebalancing |
        """)

    # Chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": (
                "Hello! I'm your AI portfolio advisor powered by Claude via MCP.\n\n"
                "I can help you:\n"
                "- **Analyze risk/reward** for potential trades\n"
                "- **Review sector exposure** and concentration risk\n"
                "- **Suggest rebalancing** based on ATR regime detection\n"
                "- **Propose trades** (always requires your approval)\n\n"
                "Try asking: *\"What's the risk/reward for buying NVDA at $131 with a $120 stop and $155 target?\"*"
            )}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about your portfolio..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Demo responses based on keywords
            lp = prompt.lower()
            if "risk" in lp and "reward" in lp:
                from portfolio_tracker.engine.risk_reward import RiskRewardCalculator
                calc = RiskRewardCalculator()
                r = calc.calculate(131.0, 120.0, 155.0)
                resp = (
                    "**Risk/Reward Analysis for NVDA**\n\n"
                    f"| Parameter | Value |\n|---|---|\n"
                    f"| Entry | ${r.entry_price} |\n"
                    f"| Stop Loss | ${r.stop_loss_price} |\n"
                    f"| Target | ${r.target_price} |\n"
                    f"| Risk per share | ${r.potential_risk} |\n"
                    f"| Reward per share | ${r.potential_reward} |\n"
                    f"| **R/R Ratio** | **{r.ratio:.2f}** |\n"
                    f"| Status | {'PASSED' if r.passed else 'BLOCKED'} |\n\n"
                    f"_{r.message}_\n\n"
                    f"*Tool used: `analyze_risk_reward(131.0, 120.0, 155.0)`*"
                )
            elif "sector" in lp or "exposure" in lp or "concentration" in lp:
                df = _compute_portfolio_df()
                total = df["Market Value"].sum()
                sector_pct = df.groupby("Sector")["Market Value"].sum() / total * 100
                lines = "\n".join(f"| {s} | {v:.1f}% |" for s, v in sector_pct.items())
                tech_pct = sector_pct.get("Technology", 0)
                risk = "HIGH" if tech_pct > 40 else "MEDIUM" if tech_pct > 25 else "LOW"
                resp = (
                    "**Sector Exposure Analysis**\n\n"
                    f"| Sector | Weight |\n|---|---|\n{lines}\n\n"
                    f"**Concentration Risk: {risk}**\n\n"
                    f"Technology sector at {tech_pct:.1f}% exceeds the 30% diversification guideline. "
                    f"Consider reducing tech exposure by 5-10% and reallocating to Healthcare or Fixed Income.\n\n"
                    f"*Tool used: `get_sector_exposure()`*"
                )
            elif "rebalance" in lp:
                resp = (
                    "**Regime-Aware Rebalance Suggestion**\n\n"
                    "ATR analysis indicates **moderate volatility** \u2014 rebalancing is appropriate.\n\n"
                    "| Symbol | Action | Shares | Reason |\n|---|---|---|---|\n"
                    "| NVDA | SELL | 30 | Overweight by 3.2% |\n"
                    "| BND | BUY | 50 | Underweight by 2.8% |\n"
                    "| JNJ | BUY | 15 | Underweight by 1.5% |\n\n"
                    "All proposed trades have R/R \u2265 2.0. Click **Confirm** in the Trading Terminal to execute.\n\n"
                    "*Tools used: `get_sector_exposure()`, `calculate_atr()`, `propose_trade()`*"
                )
            else:
                resp = (
                    "I can help with that! Here are some things you can ask:\n\n"
                    "- *\"Analyze risk/reward for buying AAPL at $227\"*\n"
                    "- *\"What's my sector exposure?\"*\n"
                    "- *\"Suggest rebalancing actions\"*\n"
                    "- *\"Calculate ATR for NVDA\"*\n\n"
                    "Each response uses MCP tools to access your portfolio data."
                )
            st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})

    # Quick actions
    st.divider()
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        if st.button("Analyze Risk/Reward"):
            st.session_state.messages.append({"role": "user", "content": "Analyze risk/reward for buying NVDA at $131 with stop at $120 and target $155"})
            st.rerun()
    with col_q2:
        if st.button("Sector Exposure"):
            st.session_state.messages.append({"role": "user", "content": "What's my current sector exposure and concentration risk?"})
            st.rerun()
    with col_q3:
        if st.button("Rebalance"):
            st.session_state.messages.append({"role": "user", "content": "Suggest rebalancing actions based on current market conditions"})
            st.rerun()
