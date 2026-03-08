"""Rebalance page — current vs target weights, one-click rebalance."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render():
    st.title("Portfolio Rebalance")

    portfolios = st.session_state.get("portfolios", [])
    if not portfolios:
        st.info("Create a portfolio first in the Portfolio Builder.")
        return

    names = [p["name"] for p in portfolios]
    selected = st.selectbox("Select Portfolio", names)
    portfolio = next(p for p in portfolios if p["name"] == selected)
    targets = portfolio["targets"]

    if not targets:
        st.warning("No targets defined for this portfolio.")
        return

    # Simulated current positions (in production: from IBKR)
    st.subheader("Rebalance Analysis")
    st.info("Connect to IBKR for live position data. Showing simulated comparison.")

    # Demo: slightly drifted from target
    import random
    random.seed(42)
    data = []
    for t in targets:
        current_w = t["weight"] + random.uniform(-0.05, 0.05)
        current_w = max(0, min(1, current_w))
        drift = current_w - t["weight"]
        action = "BUY" if drift < -0.01 else ("SELL" if drift > 0.01 else "HOLD")
        data.append({
            "Symbol": t["symbol"],
            "Target %": round(t["weight"] * 100, 1),
            "Current %": round(current_w * 100, 1),
            "Drift %": round(drift * 100, 1),
            "Action": action,
        })

    df = pd.DataFrame(data)

    # Color-coded comparison chart
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Target", x=df["Symbol"], y=df["Target %"], marker_color="steelblue"))
    fig.add_trace(go.Bar(name="Current", x=df["Symbol"], y=df["Current %"], marker_color="coral"))
    fig.update_layout(barmode="group", title="Target vs Current Allocation", yaxis_title="Weight (%)")
    st.plotly_chart(fig, use_container_width=True)

    # Rebalance actions table
    st.subheader("Required Actions")
    actions_df = df[df["Action"] != "HOLD"]
    if actions_df.empty:
        st.success("Portfolio is within tolerance. No rebalancing needed.")
    else:
        st.dataframe(actions_df, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            tolerance = st.slider("Drift Tolerance (%)", 0.5, 5.0, 1.0, 0.5)
        with col2:
            st.write("")
            st.write("")
            if st.button("Generate Rebalance Orders", type="primary"):
                st.info("Rebalance orders generated as Candidate Orders (pending risk validation).")
                st.json([
                    {"symbol": row["Symbol"], "action": row["Action"], "drift": row["Drift %"]}
                    for _, row in actions_df.iterrows()
                ])
