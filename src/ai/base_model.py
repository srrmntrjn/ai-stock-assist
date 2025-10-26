"""Abstract base interface for AI trading models."""

from abc import ABC, abstractmethod


class BaseAIModel(ABC):
    """Abstract base class for AI trading models."""

    @abstractmethod
    async def get_trading_decision(self, system_prompt: str) -> str:
        """Get a trading decision from the AI model."""

        raise NotImplementedError
