"""OpenAI (GPT) AI model implementation."""

import asyncio
import textwrap

import openai

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


class OpenAIModel(BaseAIModel):
    """OpenAI (GPT) AI model implementation."""

    def __init__(self) -> None:
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4-turbo-preview"
        log.info("OpenAI AI model initialized")

    async def get_trading_decision(self, system_prompt: str) -> str:
        """Get a trading decision from OpenAI."""

        try:
            completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": _USER_MESSAGE},
                ],
                temperature=0.7,
                max_tokens=1024,
            )

            response_text = ""
            if getattr(completion, "choices", None):
                first_choice = completion.choices[0]
                message = getattr(first_choice, "message", None)
                if message is not None:
                    response_text = getattr(message, "content", "") or ""

            if not response_text:
                log.warning("OpenAI response was empty")

            log.info("OpenAI response received: {} chars", len(response_text))
            log.debug("Raw OpenAI response: {}", response_text)

            return response_text
        except Exception as exc:  # pragma: no cover - depends on external API
            log.exception("Error calling OpenAI API: {}", exc)
            raise
