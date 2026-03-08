"""Portfolio Builder page — create, import, and manage portfolios."""

import streamlit as st

from portfolio_tracker.orchestrator.portfolio_builder import PORTFOLIO_TEMPLATES


def render():
    st.title("Portfolio Builder")

    tab1, tab2, tab3 = st.tabs(["Create from Template", "Build Custom", "Import from IBKR"])

    # --- Tab 1: Template ---
    with tab1:
        st.subheader("Start from a Template")
        template_name = st.selectbox("Choose a template", list(PORTFOLIO_TEMPLATES.keys()))

        if template_name:
            targets = PORTFOLIO_TEMPLATES[template_name]
            st.write(f"**{template_name}** — {len(targets)} holdings")

            for t in targets:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{t['symbol']}**")
                with col2:
                    st.write(f"{t['weight'] * 100:.1f}%")

            custom_name = st.text_input("Portfolio name", value=template_name)
            if st.button("Create Portfolio from Template", key="create_template"):
                if "portfolios" not in st.session_state:
                    st.session_state.portfolios = []
                st.session_state.portfolios.append({
                    "name": custom_name,
                    "targets": targets,
                    "holdings": [],
                })
                st.success(f"Portfolio '{custom_name}' created with {len(targets)} targets!")

    # --- Tab 2: Custom Build ---
    with tab2:
        st.subheader("Build a Custom Portfolio")
        portfolio_name = st.text_input("Portfolio Name", value="My Portfolio")

        if "custom_targets" not in st.session_state:
            st.session_state.custom_targets = []

        # Add symbol
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_symbol = st.text_input("Ticker Symbol", placeholder="AAPL").upper()
        with col2:
            new_weight = st.number_input("Weight (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
        with col3:
            st.write("")  # Spacer
            st.write("")
            if st.button("Add"):
                if new_symbol:
                    st.session_state.custom_targets.append({
                        "symbol": new_symbol,
                        "weight": new_weight / 100,
                    })

        # Display current targets
        if st.session_state.custom_targets:
            total_weight = sum(t["weight"] for t in st.session_state.custom_targets)
            st.write(f"**Total weight: {total_weight * 100:.1f}%**")

            if abs(total_weight - 1.0) > 0.01:
                st.warning(f"Weights should sum to 100%. Currently: {total_weight * 100:.1f}%")

            for i, t in enumerate(st.session_state.custom_targets):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{t['symbol']}**")
                with col2:
                    st.write(f"{t['weight'] * 100:.1f}%")
                with col3:
                    if st.button("Remove", key=f"rm_{i}"):
                        st.session_state.custom_targets.pop(i)
                        st.rerun()

            if st.button("Create Custom Portfolio"):
                if "portfolios" not in st.session_state:
                    st.session_state.portfolios = []
                st.session_state.portfolios.append({
                    "name": portfolio_name,
                    "targets": st.session_state.custom_targets.copy(),
                    "holdings": [],
                })
                st.session_state.custom_targets = []
                st.success(f"Portfolio '{portfolio_name}' created!")

    # --- Tab 3: IBKR Import ---
    with tab3:
        st.subheader("Import from Interactive Brokers")
        connected = st.session_state.get("ibkr_connected", False)

        if connected:
            if st.button("Sync Positions from IBKR"):
                st.info("Importing positions from IBKR account...")
                # In production: calls ibkr_client.get_portfolio()
                st.success("Positions imported successfully!")
        else:
            st.warning("Connect to IBKR first (start TWS/IB Gateway and configure .env)")
            st.code("IBKR_HOST=127.0.0.1\nIBKR_PORT=7497", language="bash")

    # --- Show existing portfolios ---
    st.divider()
    st.subheader("Your Portfolios")
    portfolios = st.session_state.get("portfolios", [])
    if portfolios:
        for i, p in enumerate(portfolios):
            with st.expander(f"{p['name']} ({len(p['targets'])} targets)"):
                for t in p["targets"]:
                    st.write(f"  {t['symbol']}: {t['weight'] * 100:.1f}%")
                if st.button("Delete", key=f"del_{i}"):
                    portfolios.pop(i)
                    st.rerun()
    else:
        st.info("No portfolios yet. Create one above!")
