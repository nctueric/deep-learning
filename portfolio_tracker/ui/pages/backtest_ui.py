"""Backtest UI page — run and visualize backtests."""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from portfolio_tracker.backtest.data_replay import DataReplaySimulator, MarketEvent
from portfolio_tracker.backtest.virtual_exchange import VirtualExchange
from portfolio_tracker.backtest.runner import BacktestRunner, BacktestConfig
from portfolio_tracker.engine.indicators import TechnicalIndicators


def _demo_strategy(event: MarketEvent, history: dict, exchange: VirtualExchange, indicators: TechnicalIndicators):
    """Demo strategy: SMA crossover with ATR stop-loss."""
    closes = history.get(event.symbol, [])
    if len(closes) < 50:
        return

    close_arr = np.array(closes)
    sma_12 = np.mean(close_arr[-12:])
    sma_50 = np.mean(close_arr[-50:])

    pos = exchange.positions.get(event.symbol)
    has_position = pos is not None and pos.quantity > 0

    # Buy signal: short MA crosses above long MA
    if not has_position and sma_12 > sma_50:
        qty = int(exchange.cash * 0.1 / event.close)
        if qty > 0:
            exchange.submit_order(event.symbol, "BUY", qty)
            # ATR-based stop
            if len(closes) >= 14:
                # Simplified ATR
                recent = close_arr[-14:]
                atr = np.mean(np.abs(np.diff(recent)))
                stop_price = event.close - 2.0 * atr
                exchange.submit_order(event.symbol, "SELL", qty, stop_price=stop_price)

    # Sell signal: short MA crosses below long MA
    elif has_position and sma_12 < sma_50:
        exchange.submit_order(event.symbol, "SELL", pos.quantity)


def render():
    st.title("Strategy Backtesting")

    col1, col2 = st.columns([1, 1])

    with col1:
        symbol = st.text_input("Symbol", value="AAPL")
        initial_cash = st.number_input("Initial Cash", value=100000, step=10000)
        days = st.slider("Backtest Period (days)", 60, 500, 252)

    with col2:
        rr_threshold = st.number_input("Min R/R Ratio", value=2.0, step=0.1)
        atr_mult = st.slider("ATR Multiplier", 1.5, 3.0, 2.0, 0.1)
        slippage = st.number_input("Slippage (bps)", value=5.0, step=1.0)

    if st.button("Run Backtest", type="primary"):
        with st.spinner("Running event-driven backtest..."):
            # Generate synthetic data for demo
            np.random.seed(42)
            close = np.cumsum(np.random.randn(days) * 2) + 150
            close = np.maximum(close, 10)
            high = close + np.abs(np.random.randn(days)) * 3
            low = close - np.abs(np.random.randn(days)) * 3
            low = np.maximum(low, 1)
            open_p = close + np.random.randn(days) * 1
            volume = np.random.randint(1_000_000, 50_000_000, days)
            timestamps = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(days)]

            # Set up simulator
            sim = DataReplaySimulator(symbols=[symbol])
            sim.load_from_arrays(symbol, timestamps, open_p, high, low, close, volume)

            # Run
            config = BacktestConfig(
                initial_cash=initial_cash,
                slippage_bps=slippage,
                risk_reward_threshold=rr_threshold,
                atr_multiplier=atr_mult,
            )
            runner = BacktestRunner(config)
            report = runner.run(sim, _demo_strategy)

        # Display results
        st.subheader("Performance Summary")

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Total Return", f"{report.total_return_pct:.1f}%")
        with col_b:
            st.metric("Sharpe Ratio", f"{report.sharpe_ratio:.2f}")
        with col_c:
            st.metric("Max Drawdown", f"{report.max_drawdown_pct:.1f}%")
        with col_d:
            st.metric("Win Rate", f"{report.win_rate_pct:.1f}%")

        col_e, col_f, col_g, col_h = st.columns(4)
        with col_e:
            st.metric("Total Trades", report.total_trades)
        with col_f:
            st.metric("Profit Factor", f"{report.profit_factor:.2f}" if report.profit_factor != float("inf") else "N/A")
        with col_g:
            st.metric("Total Commission", f"${report.total_commission:,.2f}")
        with col_h:
            st.metric("Final Equity", f"${report.final_equity:,.2f}")

        # Equity curve
        if report.equity_curve:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=report.timestamps,
                y=report.equity_curve,
                mode="lines",
                name="Equity",
                line=dict(color="steelblue", width=2),
                fill="tozeroy",
                fillcolor="rgba(70,130,180,0.1)",
            ))
            fig.add_hline(y=initial_cash, line_dash="dash", line_color="gray", annotation_text="Starting Capital")
            fig.update_layout(title="Equity Curve", xaxis_title="Date", yaxis_title="Portfolio Value ($)", height=400)
            st.plotly_chart(fig, use_container_width=True)
