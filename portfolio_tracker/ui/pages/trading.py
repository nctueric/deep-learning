"""Trading Terminal — interactive charting with risk-aware order form."""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from decimal import Decimal

from portfolio_tracker.engine.risk_reward import RiskRewardCalculator
from portfolio_tracker.engine.dynamic_stop import DynamicStopCalculator


def render():
    st.title("Trading Terminal")

    col_chart, col_order = st.columns([2, 1])

    # --- Chart Area ---
    with col_chart:
        symbol = st.text_input("Symbol", value="AAPL").upper()
        timeframe = st.segmented_control("Timeframe", ["1D", "1H", "15M", "5M"], default="1D")

        # Generate demo candlestick data (in production: from IBKR historical data)
        np.random.seed(42)
        n = 100
        close = np.cumsum(np.random.randn(n) * 2) + 150
        high = close + np.abs(np.random.randn(n)) * 3
        low = close - np.abs(np.random.randn(n)) * 3
        open_prices = close + np.random.randn(n) * 1
        dates = [f"2024-{(i // 30) + 1:02d}-{(i % 28) + 1:02d}" for i in range(n)]

        fig = go.Figure(data=[
            go.Candlestick(
                x=dates, open=open_prices, high=high, low=low, close=close,
                name=symbol,
            )
        ])

        # Overlay SMA 50 and SMA 200
        from portfolio_tracker.engine.indicators import TechnicalIndicators
        indicators = TechnicalIndicators()
        result = indicators.compute_all(symbol, high, low, close)

        if result.sma_50 is not None:
            fig.add_trace(go.Scatter(x=dates, y=result.sma_50, name="SMA 50", line=dict(color="orange", width=1)))
        if result.sma_200 is not None:
            fig.add_trace(go.Scatter(x=dates, y=result.sma_200, name="SMA 200", line=dict(color="blue", width=1)))

        fig.update_layout(
            title=f"{symbol} — {timeframe}",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Indicator summary
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("SMA 50", f"${result.latest_sma_50:.2f}" if result.latest_sma_50 else "N/A")
        with col_b:
            st.metric("SMA 200", f"${result.latest_sma_200:.2f}" if result.latest_sma_200 else "N/A")
        with col_c:
            st.metric("EMA 12", f"${result.latest_ema_12:.2f}" if result.latest_ema_12 else "N/A")
        with col_d:
            st.metric("ATR 14", f"${result.latest_atr:.2f}" if result.latest_atr else "N/A")

    # --- Risk-Aware Order Form ---
    with col_order:
        st.subheader("Place Order")

        action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
        quantity = st.number_input("Shares", min_value=1, value=10, step=1)
        entry_price = st.number_input("Entry Price", min_value=0.01, value=float(close[-1]), step=0.01)
        target_price = st.number_input("Target Price", min_value=0.01, value=float(entry_price * 1.10), step=0.01)

        # ATR-based stop suggestion
        use_atr_stop = st.checkbox("Use ATR Dynamic Stop", value=True)
        atr_multiplier = st.slider("ATR Multiplier", 1.5, 3.0, 2.0, 0.1) if use_atr_stop else None

        if use_atr_stop and result.latest_atr:
            stop_calc = DynamicStopCalculator()
            stop_result = stop_calc.calculate_from_atr(symbol, entry_price, result.latest_atr, atr_multiplier)
            stop_loss = float(stop_result.stop_price)
            st.info(f"ATR Stop: ${stop_loss:.2f} ({stop_result.stop_pct}% below entry)")
        else:
            stop_loss = st.number_input("Stop Loss", min_value=0.01, value=float(entry_price * 0.95), step=0.01)

        # Real-time R/R calculation
        rr_calc = RiskRewardCalculator()
        rr_result = rr_calc.calculate(entry_price, stop_loss, target_price)

        st.divider()
        st.write("**Risk Analysis**")

        rr_color = "green" if rr_result.passed else "red"
        st.markdown(f"Risk/Reward Ratio: :{rr_color}[**{rr_result.ratio:.2f}**]")
        st.write(f"Max Loss: ${float(rr_result.potential_risk) * quantity:,.2f}")
        st.write(f"Max Gain: ${float(rr_result.potential_reward) * quantity:,.2f}")

        if rr_result.passed:
            st.success(rr_result.message)
            if st.button("Submit Order", type="primary"):
                st.info("Order submitted (requires IBKR connection for live execution)")
        else:
            st.error(rr_result.message)
            st.button("Submit Order", type="primary", disabled=True)
            st.caption("Order blocked — R/R ratio below minimum threshold")
