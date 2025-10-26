"""AI module package for model integrations, prompt builders, and AI model factory."""

from src.ai.base_model import BaseAIModel
from src.ai.claude_model import ClaudeModel
from src.ai.mock_model import MockAIModel
from src.ai.openai_model import OpenAIModel
from src.config import settings


def get_ai_model() -> BaseAIModel:
    """Factory function that returns the configured AI model."""

    if settings.ai_model == "mock":
        return MockAIModel()
    if settings.ai_model == "claude":
        return ClaudeModel()
    if settings.ai_model == "openai":
        return OpenAIModel()
    raise ValueError(f"Unknown AI model: {settings.ai_model}")


__all__ = ["get_ai_model", "BaseAIModel"]
