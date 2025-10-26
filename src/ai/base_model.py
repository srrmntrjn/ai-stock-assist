"""Base interfaces for AI trading models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAIModel(ABC):
    """Abstract AI model capable of returning trading decisions."""

    @abstractmethod
    async def get_trading_decision(self, system_prompt: str) -> Any:
        """Return a trading decision in response to ``system_prompt``."""


__all__ = ["BaseAIModel"]
