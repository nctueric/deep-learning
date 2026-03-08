"""Dashboard page — KPI summary cards with real-time updates."""

import streamlit as st


def render():
    st.title("Portfolio Dashboard")

    # KPI Cards Row
    col1, col2, col3, col4 = st.columns(4)

    # Placeholder values — in production, fetched via WebSocket from IBKR
    nlv = st.session_state.get("nlv", 100000.00)
    daily_pnl = st.session_state.get("daily_pnl", 0.00)
    unrealized_pnl = st.session_state.get("unrealized_pnl", 0.00)
    available_funds = st.session_state.get("available_funds", 100000.00)

    with col1:
        st.metric("Net Liquidation Value", f"${nlv:,.2f}")
    with col2:
        st.metric("Daily P&L", f"${daily_pnl:,.2f}", delta=f"{daily_pnl:,.2f}")
    with col3:
        st.metric("Unrealized P&L", f"${unrealized_pnl:,.2f}", delta=f"{unrealized_pnl:,.2f}")
    with col4:
        st.metric("Available Funds", f"${available_funds:,.2f}")

    st.divider()

    # Connection status
    connected = st.session_state.get("ibkr_connected", False)
    if connected:
        st.success("Connected to IBKR")
    else:
        st.warning("Not connected to IBKR. Using demo data.")
        st.info("Configure IBKR connection in `.env` and start TWS/IB Gateway to enable live trading.")

    # Positions table
    st.subheader("Current Positions")
    positions = st.session_state.get("positions", [])
    if positions:
        st.dataframe(positions, use_container_width=True)
    else:
        st.info("No positions. Use the Portfolio Builder to create your portfolio.")
