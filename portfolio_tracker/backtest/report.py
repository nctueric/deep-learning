"""Backtest performance report — Sharpe, Max Drawdown, Win Rate, PnL distribution."""

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from portfolio_tracker.backtest.virtual_exchange import VirtualOrder


@dataclass
class BacktestReport:
    """Complete backtest performance report."""

    # Time range
    start_date: datetime | None = None
    end_date: datetime | None = None
    total_days: int = 0

    # Returns
    total_return_pct: float = 0.0
    annualized_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0

    # Drawdown
    max_drawdown_pct: float = 0.0
    max_drawdown_duration_days: int = 0

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    # Costs
    total_commission: float = 0.0
    total_slippage: float = 0.0

    # Equity
    initial_equity: float = 0.0
    final_equity: float = 0.0
    equity_curve: list[float] = field(default_factory=list)
    timestamps: list[datetime] = field(default_factory=list)


def compute_report(
    equity_curve: np.ndarray,
    timestamps: list[datetime],
    filled_orders: list[VirtualOrder],
    initial_cash: float,
    total_commission: float,
) -> BacktestReport:
    """Compute a full backtest report from equity curve and trade data."""
    report = BacktestReport()

    if len(equity_curve) == 0:
        return report

    report.start_date = timestamps[0] if timestamps else None
    report.end_date = timestamps[-1] if timestamps else None
    report.total_days = (report.end_date - report.start_date).days if report.start_date and report.end_date else 0
    report.initial_equity = initial_cash
    report.final_equity = float(equity_curve[-1])
    report.equity_curve = equity_curve.tolist()
    report.timestamps = timestamps
    report.total_commission = total_commission

    # Returns
    report.total_return_pct = (report.final_equity / report.initial_equity - 1) * 100

    if report.total_days > 0:
        years = report.total_days / 365.25
        report.annualized_return_pct = ((report.final_equity / report.initial_equity) ** (1 / years) - 1) * 100 if years > 0 else 0

    # Daily returns for Sharpe/Sortino
    if len(equity_curve) > 1:
        daily_returns = np.diff(equity_curve) / equity_curve[:-1]
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)

        report.sharpe_ratio = float(mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0

        downside_returns = daily_returns[daily_returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        report.sortino_ratio = float(mean_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0

    # Max Drawdown
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = (equity_curve - running_max) / running_max
    report.max_drawdown_pct = float(np.min(drawdowns) * 100)

    # Drawdown duration
    in_drawdown = drawdowns < 0
    if np.any(in_drawdown):
        dd_starts = np.where(np.diff(in_drawdown.astype(int)) == 1)[0]
        dd_ends = np.where(np.diff(in_drawdown.astype(int)) == -1)[0]
        if len(dd_starts) > 0 and len(dd_ends) > 0:
            max_duration = max(dd_ends[i] - dd_starts[i] for i in range(min(len(dd_starts), len(dd_ends))))
            report.max_drawdown_duration_days = int(max_duration)

    # Trade statistics
    buy_orders = [o for o in filled_orders if o.action == "BUY"]
    sell_orders = [o for o in filled_orders if o.action == "SELL"]

    # Match buy/sell pairs for PnL
    wins = []
    losses = []
    total_slippage = 0.0

    for sell in sell_orders:
        matching_buys = [b for b in buy_orders if b.symbol == sell.symbol]
        if matching_buys:
            buy = matching_buys[0]
            pnl = (sell.fill_price - buy.fill_price) * sell.quantity - sell.commission - buy.commission
            if pnl > 0:
                wins.append(pnl)
            else:
                losses.append(pnl)

    for order in filled_orders:
        total_slippage += order.slippage

    report.total_trades = len(sell_orders)
    report.winning_trades = len(wins)
    report.losing_trades = len(losses)
    report.win_rate_pct = (len(wins) / len(sell_orders) * 100) if sell_orders else 0
    report.avg_win = float(np.mean(wins)) if wins else 0
    report.avg_loss = float(np.mean(losses)) if losses else 0
    report.profit_factor = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else float("inf") if wins else 0
    report.total_slippage = total_slippage

    return report
