"""Trade History page — execution log and equity curve."""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd


def render():
    st.title("Trade History")

    tab1, tab2 = st.tabs(["Execution Log", "Equity Curve"])

    with tab1:
        st.subheader("Trade Executions")
        trades = st.session_state.get("trades", [])
        if trades:
            st.dataframe(pd.DataFrame(trades), use_container_width=True)
        else:
            st.info("No trades executed yet. History will appear here once you start trading.")

            # Demo data
            st.subheader("Demo Execution Log")
            demo = pd.DataFrame([
                {"Date": "2024-01-15", "Symbol": "AAPL", "Action": "BUY", "Qty": 50, "Price": 185.50, "R/R": 2.5, "Status": "FILLED"},
                {"Date": "2024-02-01", "Symbol": "MSFT", "Action": "BUY", "Qty": 30, "Price": 397.20, "R/R": 3.1, "Status": "FILLED"},
                {"Date": "2024-02-15", "Symbol": "AAPL", "Action": "SELL", "Qty": 25, "Price": 192.80, "R/R": "-", "Status": "FILLED"},
            ])
            st.dataframe(demo, use_container_width=True)

    with tab2:
        st.subheader("Portfolio Equity Curve")

        # Demo equity curve (in production: from portfolio_snapshots table)
        np.random.seed(123)
        days = 252
        returns = np.random.randn(days) * 0.01 + 0.0003
        equity = 100000 * np.cumprod(1 + returns)
        dates = pd.date_range("2024-01-01", periods=days, freq="B")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=equity,
            mode="lines",
            name="Portfolio Value",
            line=dict(color="steelblue", width=2),
            fill="tozeroy",
            fillcolor="rgba(70,130,180,0.1)",
        ))
        fig.update_layout(
            title="Portfolio Net Liquidation Value",
            xaxis_title="Date",
            yaxis_title="Value ($)",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        total_return = (equity[-1] / equity[0] - 1) * 100
        max_dd = np.min(equity / np.maximum.accumulate(equity) - 1) * 100
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)

        with col1:
            st.metric("Total Return", f"{total_return:.1f}%")
        with col2:
            st.metric("Max Drawdown", f"{max_dd:.1f}%")
        with col3:
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")
        with col4:
            st.metric("Win Rate", "58.3%")
