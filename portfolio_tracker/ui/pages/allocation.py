"""Allocation page — visual weight editor with real-time pie chart."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render():
    st.title("Portfolio Allocation")

    portfolios = st.session_state.get("portfolios", [])
    if not portfolios:
        st.info("Create a portfolio first in the Portfolio Builder.")
        return

    # Select portfolio
    names = [p["name"] for p in portfolios]
    selected = st.selectbox("Select Portfolio", names)
    portfolio = next(p for p in portfolios if p["name"] == selected)
    targets = portfolio["targets"]

    if not targets:
        st.warning("This portfolio has no target allocations.")
        return

    col_chart, col_edit = st.columns([1, 1])

    # --- Pie/Sunburst Chart ---
    with col_chart:
        st.subheader("Target Allocation")
        df = pd.DataFrame(targets)
        df["weight_pct"] = df["weight"] * 100

        fig = px.pie(
            df,
            values="weight_pct",
            names="symbol",
            title=f"{selected} — Target Allocation",
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="label+percent")
        st.plotly_chart(fig, use_container_width=True)

    # --- Weight Sliders ---
    with col_edit:
        st.subheader("Adjust Weights")
        updated_targets = []
        for t in targets:
            new_weight = st.slider(
                f"{t['symbol']}",
                min_value=0.0,
                max_value=100.0,
                value=float(t["weight"] * 100),
                step=0.5,
                key=f"slider_{t['symbol']}",
            )
            updated_targets.append({"symbol": t["symbol"], "weight": new_weight / 100})

        total = sum(t["weight"] for t in updated_targets)
        st.write(f"**Total: {total * 100:.1f}%**")
        if abs(total - 1.0) > 0.01:
            st.warning("Weights should sum to 100%")

        if st.button("Save Weights"):
            portfolio["targets"] = updated_targets
            st.success("Weights updated!")
            st.rerun()

    # --- Current vs Target comparison ---
    st.divider()
    st.subheader("Current vs Target Weights")

    # Simulated current weights (in production, from IBKR positions)
    current = st.session_state.get("current_weights", {})
    if current:
        comparison_data = []
        for t in targets:
            comparison_data.append({
                "Symbol": t["symbol"],
                "Target %": t["weight"] * 100,
                "Current %": current.get(t["symbol"], 0) * 100,
                "Drift %": (current.get(t["symbol"], 0) - t["weight"]) * 100,
            })
        df_compare = pd.DataFrame(comparison_data)

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Target", x=df_compare["Symbol"], y=df_compare["Target %"], marker_color="steelblue"))
        fig.add_trace(go.Bar(name="Current", x=df_compare["Symbol"], y=df_compare["Current %"], marker_color="coral"))
        fig.update_layout(barmode="group", title="Target vs Current Allocation")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Connect to IBKR to see current vs target weight comparison.")
