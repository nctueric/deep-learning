"""AI Copilot chatbox — natural language interface to portfolio tools via MCP."""

import streamlit as st
import json


def render():
    st.title("AI Copilot")

    st.info(
        "Chat with your AI portfolio advisor. The AI can read your portfolio data, "
        "compute technical indicators, analyze risk/reward, and propose trades for your review."
    )

    # LLM configuration
    with st.sidebar:
        st.subheader("AI Settings")
        provider = st.selectbox("LLM Provider", ["Anthropic (Claude)", "OpenAI"])
        api_key = st.text_input("API Key", type="password")
        if not api_key:
            st.warning("Enter your API key to enable AI features.")

    # Chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm your AI portfolio advisor. I can help you:\n\n"
             "- **Analyze risk/reward** for potential trades\n"
             "- **Review sector exposure** and concentration risk\n"
             "- **Suggest rebalancing** actions based on market conditions\n"
             "- **Propose trades** (with your approval required)\n\n"
             "What would you like to know about your portfolio?"}
        ]

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your portfolio..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if not api_key:
                response = "Please configure your API key in the sidebar to enable AI analysis."
            else:
                response = _process_query(prompt, api_key, provider)
            st.markdown(response)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})

    # Quick action buttons
    st.divider()
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Analyze Portfolio Risk"):
            _add_quick_action("Analyze my current portfolio's sector exposure and overall risk level.")
    with col2:
        if st.button("Check R/R for AAPL"):
            _add_quick_action("Analyze the risk/reward for buying AAPL at current price with a 5% stop loss and 15% target.")
    with col3:
        if st.button("Rebalance Suggestion"):
            _add_quick_action("Review my portfolio and suggest rebalancing actions based on current market conditions.")

    # MCP tools available
    with st.expander("Available AI Tools (MCP)"):
        st.markdown("""
        | Tool | Description |
        |---|---|
        | `calculate_atr` | Compute ATR for volatility assessment |
        | `analyze_risk_reward` | Check R/R ratio for trade proposals |
        | `propose_trade` | Propose a trade (requires your approval) |
        | `get_sector_exposure` | View portfolio sector breakdown |
        """)


def _add_quick_action(query: str):
    """Add a quick action query to the chat."""
    st.session_state.chat_messages.append({"role": "user", "content": query})
    st.rerun()


def _process_query(query: str, api_key: str, provider: str) -> str:
    """Process a user query through the LLM with MCP tools.

    In production, this connects to Claude/OpenAI via MCP client,
    giving the LLM access to portfolio tools.
    """
    # Demo response — in production, this calls the LLM API with MCP tools
    query_lower = query.lower()

    if "risk" in query_lower and "reward" in query_lower:
        from portfolio_tracker.engine.risk_reward import RiskRewardCalculator
        calc = RiskRewardCalculator()
        # Demo calculation
        result = calc.calculate(150.0, 142.5, 172.5)
        return (
            f"**Risk/Reward Analysis**\n\n"
            f"- Entry: ${result.entry_price}\n"
            f"- Stop Loss: ${result.stop_loss_price}\n"
            f"- Target: ${result.target_price}\n"
            f"- **R/R Ratio: {result.ratio:.2f}**\n"
            f"- Status: {'PASSED' if result.passed else 'BLOCKED'}\n\n"
            f"_{result.message}_"
        )

    if "rebalance" in query_lower:
        return (
            "**Rebalance Analysis**\n\n"
            "Based on current market conditions:\n"
            "- ATR indicates **moderate volatility** — rebalancing is appropriate\n"
            "- Your tech sector allocation has drifted +3.2% above target\n"
            "- Recommendation: Reduce QQQ by 2% and increase BND by 2%\n\n"
            "_Note: Connect to IBKR for live analysis. This is a demo response._"
        )

    return (
        "I can help with that! To provide live analysis, please:\n"
        "1. Configure your LLM API key in the sidebar\n"
        "2. Connect to IBKR for real portfolio data\n\n"
        "_This is a demo response. In production, I connect to your portfolio via MCP tools._"
    )
