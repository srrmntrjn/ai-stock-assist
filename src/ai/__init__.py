"""AI model factory and exports."""

from src.ai.base_model import BaseAIModel
from src.ai.claude_model import ClaudeModel
from src.ai.openai_model import OpenAIModel
from src.config import settings


def get_ai_model() -> BaseAIModel:
    """Factory function that returns the configured AI model."""

    if settings.ai_model == "claude":
        return ClaudeModel()
    if settings.ai_model == "openai":
        return OpenAIModel()
    raise ValueError(f"Unknown AI model: {settings.ai_model}")
