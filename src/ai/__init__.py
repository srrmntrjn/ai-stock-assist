"""AI model helpers."""

from src.ai.base_model import BaseAIModel
from src.ai.mock_model import MockAIModel


def get_ai_model() -> BaseAIModel:
    """Return the configured AI model instance.

    The real model integrations are not yet implemented, so for now we use a
    deterministic mock that keeps the trading loop functional without requiring
    external API calls.
    """

    return MockAIModel()


__all__ = ["get_ai_model", "BaseAIModel"]
