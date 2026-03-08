"""Service for fetching stock prices."""

import json
import urllib.request
import urllib.error
from typing import Optional


class PriceService:
    """Fetches current stock prices. Uses Yahoo Finance API as a free data source."""

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    def get_price(self, symbol: str) -> Optional[float]:
        """Fetch current price for a single symbol. Returns None if unavailable."""
        try:
            url = self.BASE_URL.format(symbol=symbol.upper())
            req = urllib.request.Request(url, headers={"User-Agent": "PortfolioTracker/0.1"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError):
            return None

    def get_prices(self, symbols: list[str]) -> dict[str, float]:
        """Fetch current prices for multiple symbols."""
        prices = {}
        for symbol in symbols:
            price = self.get_price(symbol)
            if price is not None:
                prices[symbol.upper()] = price
        return prices
