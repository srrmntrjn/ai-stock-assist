"""Claude (Anthropic) AI model implementation."""

import asyncio
import textwrap

import anthropic

from src.ai.base_model import BaseAIModel
from src.config import settings
from src.logger import log


_USER_MESSAGE = textwrap.dedent(
    """\
    Based on the market data and your current portfolio,
    make a trading decision for ONE coin. Respond ONLY with valid JSON in this exact format:

    {
        "symbol": "BTC-PERPETUAL",
        "action": "BUY",
        "confidence": 0.88,
        "reasoning": "Your analysis here",
        "entry_type": "MARKET",
        "entry_price": null,
        "stop_loss": 105877.7,
        "take_profit": 112253.96,
        "position_size_pct": 20
    }

    Rules:
    - action must be: BUY, SELL, or HOLD
    - confidence: 0.0 to 1.0
    - entry_type: MARKET or LIMIT
    - If MARKET, entry_price should be null
    - stop_loss and take_profit should be reasonable prices
    - position_size_pct: percentage of account to use (1-100)
    """
)


class ClaudeModel(BaseAIModel):
    """Claude (Anthropic) AI model implementation."""

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
        log.info("Claude AI model initialized")

    async def get_trading_decision(self, system_prompt: str) -> str:
        """Get a trading decision from Claude."""

        try:
            message = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": _USER_MESSAGE}],
            )

            response_text = ""
            if getattr(message, "content", None):
                first_message = message.content[0]
                response_text = getattr(first_message, "text", "")

            if not response_text:
                log.warning("Claude response was empty")

            log.info("Claude response received: {} chars", len(response_text))
            log.debug("Raw Claude response: {}", response_text)

            return response_text
        except Exception as exc:  # pragma: no cover - depends on external API
            log.exception("Error calling Claude API: {}", exc)
            raise
