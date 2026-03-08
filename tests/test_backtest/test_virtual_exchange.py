"""Tests for virtual exchange matching engine."""

from portfolio_tracker.backtest.virtual_exchange import VirtualExchange, VirtualOrderStatus
from portfolio_tracker.backtest.data_replay import MarketEvent
from datetime import datetime


def _make_event(symbol="AAPL", open_=150, high=155, low=148, close=152, volume=1000):
    return MarketEvent(
        timestamp=datetime(2024, 1, 1),
        symbol=symbol,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def test_market_order_fill():
    exchange = VirtualExchange(cash=100000, slippage_bps=0, commission_per_share=0, min_commission=0)
    order = exchange.submit_order("AAPL", "BUY", 10)
    event = _make_event(close=150)

    filled = exchange.process_event(event)

    assert len(filled) == 1
    assert filled[0].status == VirtualOrderStatus.FILLED
    assert filled[0].fill_price == 150
    assert exchange.positions["AAPL"].quantity == 10


def test_limit_order_fill():
    exchange = VirtualExchange(cash=100000, slippage_bps=0, commission_per_share=0, min_commission=0)
    exchange.submit_order("AAPL", "BUY", 10, limit_price=148)

    # Price doesn't reach limit
    event_high = _make_event(low=149)
    filled = exchange.process_event(event_high)
    assert len(filled) == 0

    # Price reaches limit
    event_low = _make_event(low=147)
    filled = exchange.process_event(event_low)
    assert len(filled) == 1


def test_stop_order_trigger():
    exchange = VirtualExchange(cash=100000, slippage_bps=0, commission_per_share=0, min_commission=0)

    # First buy
    exchange.submit_order("AAPL", "BUY", 10)
    exchange.process_event(_make_event(close=150))

    # Set stop loss
    exchange.submit_order("AAPL", "SELL", 10, stop_price=145)

    # Stop not triggered
    filled = exchange.process_event(_make_event(low=146))
    assert len(filled) == 0

    # Stop triggered
    filled = exchange.process_event(_make_event(low=144))
    assert len(filled) == 1
    assert filled[0].action == "SELL"


def test_commission_and_slippage():
    exchange = VirtualExchange(cash=100000, commission_per_share=0.005, slippage_bps=10)
    exchange.submit_order("AAPL", "BUY", 100)
    filled = exchange.process_event(_make_event(close=100))

    assert len(filled) == 1
    assert filled[0].commission > 0
    assert filled[0].slippage > 0
    # Buy slippage increases fill price
    assert filled[0].fill_price > 100


def test_portfolio_value():
    exchange = VirtualExchange(cash=100000, slippage_bps=0, commission_per_share=0, min_commission=0)
    exchange.submit_order("AAPL", "BUY", 10)
    exchange.process_event(_make_event(close=150))

    value = exchange.portfolio_value({"AAPL": 160})
    assert value == 100000 - 1500 + 1600  # cash spent + current value
