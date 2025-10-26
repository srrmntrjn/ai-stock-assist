"""Simple portfolio tracking utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np

from src.exchanges.base import Balance, Position


class PortfolioTracker:
    """Track portfolio statistics over time."""

    def __init__(self, history_file: Path | None = None) -> None:
        self.history_file = history_file or Path("data/portfolio_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._equity_curve: List[float] = self._load_history()

    def _load_history(self) -> List[float]:
        if not self.history_file.exists():
            return []
        try:
            data = json.loads(self.history_file.read_text())
            return [float(x) for x in data]
        except Exception:
            return []

    def _save_history(self) -> None:
        self.history_file.write_text(json.dumps(self._equity_curve, indent=2))

    async def update(self, balance: Balance, positions: List[Position]) -> None:
        """Record the latest account value."""

        self._equity_curve.append(balance.total)
        self._equity_curve = self._equity_curve[-500:]
        self._save_history()

    async def get_sharpe_ratio(self) -> float:
        """Return a simple Sharpe ratio estimate."""

        if len(self._equity_curve) < 2:
            return 0.0

        returns = np.diff(self._equity_curve) / np.array(self._equity_curve[:-1])
        if returns.std() == 0:
            return 0.0
        sharpe_daily = returns.mean() / returns.std() * np.sqrt(365)
        return float(np.round(sharpe_daily, 4))


__all__ = ["PortfolioTracker"]
