"""Command-line interface for Portfolio Tracker."""

import argparse
import sys

from portfolio_tracker.models.portfolio import Portfolio
from portfolio_tracker.services.storage import StorageService
from portfolio_tracker.services.price import PriceService
from portfolio_tracker.utils.formatting import format_currency, format_percentage, format_table


def get_services():
    return StorageService(), PriceService()


def cmd_buy(args):
    """Handle the buy command."""
    storage, _ = get_services()
    portfolio = storage.load()
    tx = portfolio.buy(args.symbol, args.quantity, args.price)
    storage.save(portfolio)
    print(f"Bought {tx.quantity} shares of {tx.symbol} at {format_currency(tx.price)}")
    print(f"Total: {format_currency(tx.total_value)}")


def cmd_sell(args):
    """Handle the sell command."""
    storage, _ = get_services()
    portfolio = storage.load()
    try:
        tx = portfolio.sell(args.symbol, args.quantity, args.price)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    storage.save(portfolio)
    print(f"Sold {tx.quantity} shares of {tx.symbol} at {format_currency(tx.price)}")
    print(f"Total: {format_currency(tx.total_value)}")


def cmd_show(args):
    """Show portfolio summary."""
    storage, price_service = get_services()
    portfolio = storage.load()

    if not portfolio.holdings:
        print("Portfolio is empty. Use 'buy' to add holdings.")
        return

    symbols = list(portfolio.holdings.keys())
    print("Fetching current prices...")
    prices = price_service.get_prices(symbols)

    # Fall back to avg_cost for symbols where price fetch failed
    for symbol in symbols:
        if symbol not in prices:
            prices[symbol] = portfolio.holdings[symbol].avg_cost
            print(f"  Warning: Could not fetch price for {symbol}, using avg cost")

    summary = portfolio.summary(prices)

    print(f"\n  {summary['name']}")
    print(f"  {'-' * 40}")

    headers = ["Symbol", "Qty", "Avg Cost", "Price", "Value", "Gain/Loss", "G/L %"]
    rows = []
    for h in summary["holdings"]:
        rows.append([
            h["symbol"],
            f"{h['quantity']:.2f}",
            format_currency(h["avg_cost"]),
            format_currency(h["current_price"]),
            format_currency(h["market_value"]),
            format_currency(h["gain_loss"]),
            format_percentage(h["gain_loss_pct"]),
        ])

    print(format_table(headers, rows))
    print()
    print(f"  Total Cost Basis:  {format_currency(summary['total_cost_basis'])}")
    print(f"  Total Value:       {format_currency(summary['total_market_value'])}")
    print(f"  Total Gain/Loss:   {format_currency(summary['total_gain_loss'])} ({format_percentage(summary['total_gain_loss_pct'])})")
    print(f"  Holdings: {summary['num_holdings']}  |  Transactions: {summary['num_transactions']}")


def cmd_history(args):
    """Show transaction history."""
    storage, _ = get_services()
    portfolio = storage.load()

    if not portfolio.transactions:
        print("No transactions recorded.")
        return

    headers = ["Date", "Type", "Symbol", "Qty", "Price", "Total"]
    rows = []
    for tx in portfolio.transactions:
        rows.append([
            tx.timestamp.strftime("%Y-%m-%d %H:%M"),
            tx.transaction_type.value,
            tx.symbol,
            f"{tx.quantity:.2f}",
            format_currency(tx.price),
            format_currency(tx.total_value),
        ])

    print(format_table(headers, rows))


def main():
    parser = argparse.ArgumentParser(
        prog="portfolio-tracker",
        description="Track and analyze investment portfolio performance",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # buy
    buy_parser = subparsers.add_parser("buy", help="Record a stock purchase")
    buy_parser.add_argument("symbol", help="Stock ticker symbol")
    buy_parser.add_argument("quantity", type=float, help="Number of shares")
    buy_parser.add_argument("price", type=float, help="Price per share")
    buy_parser.set_defaults(func=cmd_buy)

    # sell
    sell_parser = subparsers.add_parser("sell", help="Record a stock sale")
    sell_parser.add_argument("symbol", help="Stock ticker symbol")
    sell_parser.add_argument("quantity", type=float, help="Number of shares")
    sell_parser.add_argument("price", type=float, help="Price per share")
    sell_parser.set_defaults(func=cmd_sell)

    # show
    show_parser = subparsers.add_parser("show", help="Show portfolio summary")
    show_parser.set_defaults(func=cmd_show)

    # history
    history_parser = subparsers.add_parser("history", help="Show transaction history")
    history_parser.set_defaults(func=cmd_history)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
