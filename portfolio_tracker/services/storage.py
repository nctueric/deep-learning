"""Service for persisting portfolio data to JSON files."""

import json
from pathlib import Path

from portfolio_tracker.models.portfolio import Portfolio


DEFAULT_DATA_DIR = Path.home() / ".portfolio_tracker"
DEFAULT_FILE = "portfolio.json"


class StorageService:
    """Handles saving and loading portfolio data."""

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, filename: str = DEFAULT_FILE) -> Path:
        return self.data_dir / filename

    def save(self, portfolio: Portfolio, filename: str = DEFAULT_FILE) -> Path:
        """Save portfolio to a JSON file."""
        path = self._file_path(filename)
        with open(path, "w") as f:
            json.dump(portfolio.to_dict(), f, indent=2)
        return path

    def load(self, filename: str = DEFAULT_FILE) -> Portfolio:
        """Load portfolio from a JSON file."""
        path = self._file_path(filename)
        if not path.exists():
            return Portfolio()
        with open(path) as f:
            data = json.load(f)
        return Portfolio.from_dict(data)

    def exists(self, filename: str = DEFAULT_FILE) -> bool:
        return self._file_path(filename).exists()

    def list_portfolios(self) -> list[str]:
        """List all saved portfolio files."""
        return [f.stem for f in self.data_dir.glob("*.json")]
