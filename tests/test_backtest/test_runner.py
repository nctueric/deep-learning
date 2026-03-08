"""Tests for backtest runner."""

import numpy as np
from datetime import datetime, timedelta

from portfolio_tracker.backtest.data_replay import DataReplaySimulator, MarketEvent
from portfolio_tracker.backtest.virtual_exchange import VirtualExchange
from portfolio_tracker.backtest.runner import BacktestRunner, BacktestConfig
from portfolio_tracker.engine.indicators import TechnicalIndicators


def _simple_strategy(event: MarketEvent, history: dict, exchange: VirtualExchange, indicators: TechnicalIndicators):
    """Buy and hold strategy for testing."""
    closes = history.get(event.symbol, [])
    pos = exchange.positions.get(event.symbol)
    has_position = pos is not None and pos.quantity > 0

    if len(closes) == 5 and not has_position:  # Buy on day 5
        qty = int(exchange.cash * 0.5 / event.close)
        if qty > 0:
            exchange.submit_order(event.symbol, "BUY", qty)


def test_backtest_runs_without_error():
    np.random.seed(42)
    n = 60
    close = np.cumsum(np.random.randn(n) * 0.5) + 100
    close = np.maximum(close, 10)
    high = close + 1
    low = close - 1
    open_p = close + np.random.randn(n) * 0.3
    volume = np.random.randint(100000, 1000000, n)
    timestamps = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]

    sim = DataReplaySimulator(symbols=["TEST"])
    sim.load_from_arrays("TEST", timestamps, open_p, high, low, close, volume)

    runner = BacktestRunner(BacktestConfig(initial_cash=50000))
    report = runner.run(sim, _simple_strategy)

    assert report.initial_equity == 50000
    assert report.final_equity > 0
    assert len(report.equity_curve) == n
    assert report.total_return_pct != 0 or report.total_trades == 0
