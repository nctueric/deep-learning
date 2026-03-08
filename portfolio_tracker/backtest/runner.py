"""Backtest Runner — event-driven engine that reuses live trading logic.

Key principle: backtest and live trading share the same engine/ code,
eliminating look-ahead bias (per nautilus_trader philosophy).
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

import numpy as np

from portfolio_tracker.backtest.data_replay import DataReplaySimulator, MarketEvent
from portfolio_tracker.backtest.virtual_exchange import VirtualExchange
from portfolio_tracker.backtest.report import BacktestReport, compute_report
from portfolio_tracker.engine.indicators import TechnicalIndicators
from portfolio_tracker.engine.risk_reward import RiskRewardCalculator

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""

    initial_cash: float = 100000.0
    commission_per_share: float = 0.005
    slippage_bps: float = 5.0
    risk_reward_threshold: float = 2.0
    atr_multiplier: float = 2.0
    atr_period: int = 14


# Strategy callback type
StrategyFn = Callable[[MarketEvent, dict, VirtualExchange, TechnicalIndicators], None]


class BacktestRunner:
    """Runs event-driven backtests with pluggable strategies."""

    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()
        self.indicators = TechnicalIndicators()
        self.rr_calc = RiskRewardCalculator(self.config.risk_reward_threshold)

    def run(
        self,
        simulator: DataReplaySimulator,
        strategy: StrategyFn,
    ) -> BacktestReport:
        """Execute a backtest with the given strategy function.

        The strategy function receives:
        - event: current MarketEvent
        - history: dict of symbol -> list of past closes
        - exchange: VirtualExchange to submit orders
        - indicators: TechnicalIndicators engine
        """
        exchange = VirtualExchange(
            cash=self.config.initial_cash,
            commission_per_share=self.config.commission_per_share,
            slippage_bps=self.config.slippage_bps,
        )

        history: dict[str, list[float]] = {}
        equity_curve: list[float] = []
        timestamps: list[datetime] = []

        for event in simulator.replay():
            # Update history
            if event.symbol not in history:
                history[event.symbol] = []
            history[event.symbol].append(event.close)

            # Process pending orders
            exchange.process_event(event)

            # Call strategy
            try:
                strategy(event, history, exchange, self.indicators)
            except Exception as e:
                logger.error(f"Strategy error at {event.timestamp}: {e}")

            # Record equity
            prices = {sym: closes[-1] for sym, closes in history.items() if closes}
            equity_curve.append(exchange.portfolio_value(prices))
            timestamps.append(event.timestamp)

        return compute_report(
            equity_curve=np.array(equity_curve),
            timestamps=timestamps,
            filled_orders=exchange.filled_orders,
            initial_cash=self.config.initial_cash,
            total_commission=exchange.total_commission(),
        )

    def run_walk_forward(
        self,
        simulator: DataReplaySimulator,
        strategy: StrategyFn,
        in_sample_pct: float = 0.7,
    ) -> tuple[BacktestReport, BacktestReport]:
        """Walk-forward optimization: split data into in-sample and out-of-sample."""
        # Collect all events
        all_events = list(simulator.replay())
        split_idx = int(len(all_events) * in_sample_pct)

        # In-sample
        in_sim = DataReplaySimulator(symbols=simulator.symbols)
        for sym in simulator.symbols:
            sym_events = [e for e in all_events[:split_idx] if e.symbol == sym]
            if sym_events:
                in_sim.load_from_arrays(
                    sym,
                    [e.timestamp for e in sym_events],
                    np.array([e.open for e in sym_events]),
                    np.array([e.high for e in sym_events]),
                    np.array([e.low for e in sym_events]),
                    np.array([e.close for e in sym_events]),
                    np.array([e.volume for e in sym_events]),
                )

        # Out-of-sample
        out_sim = DataReplaySimulator(symbols=simulator.symbols)
        for sym in simulator.symbols:
            sym_events = [e for e in all_events[split_idx:] if e.symbol == sym]
            if sym_events:
                out_sim.load_from_arrays(
                    sym,
                    [e.timestamp for e in sym_events],
                    np.array([e.open for e in sym_events]),
                    np.array([e.high for e in sym_events]),
                    np.array([e.low for e in sym_events]),
                    np.array([e.close for e in sym_events]),
                    np.array([e.volume for e in sym_events]),
                )

        in_report = self.run(in_sim, strategy)
        out_report = self.run(out_sim, strategy)

        return in_report, out_report
