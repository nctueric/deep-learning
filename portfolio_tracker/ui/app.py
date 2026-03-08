"""Streamlit main application — Portfolio Tracker UI."""

import streamlit as st

st.set_page_config(
    page_title="Portfolio Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.sidebar.title("Portfolio Tracker")
    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Portfolio Builder",
            "Allocation",
            "Trading Terminal",
            "Rebalance",
            "Trade History",
            "Backtest",
            "AI Copilot",
        ],
    )

    if page == "Dashboard":
        from portfolio_tracker.ui.pages.dashboard import render
        render()
    elif page == "Portfolio Builder":
        from portfolio_tracker.ui.pages.builder import render
        render()
    elif page == "Allocation":
        from portfolio_tracker.ui.pages.allocation import render
        render()
    elif page == "Trading Terminal":
        from portfolio_tracker.ui.pages.trading import render
        render()
    elif page == "Rebalance":
        from portfolio_tracker.ui.pages.rebalance import render
        render()
    elif page == "Trade History":
        from portfolio_tracker.ui.pages.history import render
        render()
    elif page == "Backtest":
        from portfolio_tracker.ui.pages.backtest_ui import render
        render()
    elif page == "AI Copilot":
        from portfolio_tracker.ui.components.ai_chat import render
        render()


if __name__ == "__main__":
    main()
