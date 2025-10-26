"""Basic risk management helpers for the trading bot."""

from __future__ import annotations

from typing import Any, Dict

from src.config import settings
from src.logger import log


class RiskManager:
    """Validate trade recommendations before execution."""

    def validate_trade(self, decision: Dict[str, Any]) -> bool:
        """Return ``True`` if the trade passes all risk checks."""

        action = decision.get("action", "HOLD").upper()
        if action == "HOLD":
            return True

        symbol = decision.get("symbol")
        if symbol not in settings.symbol_list:
            log.warning("RiskManager rejected trade: unknown symbol %s", symbol)
            return False

        position_size = float(decision.get("position_size_pct", settings.position_size_pct) or 0)
        if position_size <= 0:
            log.warning("RiskManager rejected trade: position size must be positive")
            return False

        if position_size > settings.max_position_size_pct:
            log.warning(
                "RiskManager rejected trade: %.2f%% position exceeds limit %.2f%%",
                position_size,
                settings.max_position_size_pct,
            )
            return False

        return True


__all__ = ["RiskManager"]
