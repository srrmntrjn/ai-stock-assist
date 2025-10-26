"""Simple deterministic AI model used for local development."""

from __future__ import annotations

import json
from dataclasses import dataclass

from src.ai.base_model import BaseAIModel
from src.config import settings


@dataclass
class MockDecision:
    """Container for mock trading decisions."""

    symbol: str
    action: str = "HOLD"
    confidence: float = 0.0
    reasoning: str = (
        "Mock model in use. Configure a real AI provider to enable automated decisions."
    )
    entry_type: str = "MARKET"
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float = settings.position_size_pct

    def to_json(self) -> str:
        """Return a JSON encoded representation of the decision."""

        return json.dumps(self.__dict__)


class MockAIModel(BaseAIModel):
    """Mock AI model that keeps the trading loop operational."""

    async def get_trading_decision(self, system_prompt: str) -> str:
        """Return a HOLD decision encoded as JSON."""

        first_symbol = settings.symbol_list[0] if settings.symbol_list else "BTC-PERPETUAL"
        decision = MockDecision(symbol=first_symbol)
        return decision.to_json()


__all__ = ["MockAIModel"]
