# Task 10: AI Models Interface

**Status:** ⏭️ NEXT

**Estimated Time:** 1.5 hours

---

## Overview

Build a pluggable AI model system that supports both Claude (Anthropic) and OpenAI (GPT), with a common interface for getting trading decisions.

---

## Implementation Details

### Files

- `src/ai/base_model.py` - Abstract interface
- `src/ai/claude_model.py` - Claude implementation
- `src/ai/openai_model.py` - OpenAI implementation

---

## Base Interface

### File: `src/ai/base_model.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAIModel(ABC):
    """Abstract base class for AI trading models"""

    @abstractmethod
    async def get_trading_decision(self, system_prompt: str) -> Dict[str, Any]:
        """
        Get trading decision from AI model

        Args:
            system_prompt: Formatted market data and portfolio state

        Returns:
            {
                "symbol": "BTC-PERPETUAL",
                "action": "BUY|SELL|HOLD",
                "confidence": 0.88,
                "reasoning": "Strong momentum, MACD bullish...",
                "entry_type": "MARKET|LIMIT",
                "entry_price": 111000.0,  # Only for LIMIT
                "stop_loss": 105877.7,
                "take_profit": 112253.96,
                "position_size_pct": 20
            }
        """
        pass
```

---

## Claude Implementation

### File: `src/ai/claude_model.py`

```python
import anthropic
from src.ai.base_model import BaseAIModel
from src.config import settings
from src.logger import log

class ClaudeModel(BaseAIModel):
    """Claude (Anthropic) AI model implementation"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"  # Latest Sonnet
        log.info("Claude AI model initialized")

    async def get_trading_decision(self, system_prompt: str) -> Dict[str, Any]:
        """Get trading decision from Claude"""
        try:
            # User message asking for decision
            user_message = """Based on the market data and your current portfolio,
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

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract response
            response_text = message.content[0].text

            log.info(f"Claude response received: {len(response_text)} chars")
            log.debug(f"Raw response: {response_text}")

            # Parse JSON (handled in response_parser.py)
            return response_text

        except Exception as e:
            log.error(f"Error calling Claude API: {e}")
            raise
```

---

## OpenAI Implementation

### File: `src/ai/openai_model.py`

```python
import openai
from src.ai.base_model import BaseAIModel
from src.config import settings
from src.logger import log

class OpenAIModel(BaseAIModel):
    """OpenAI (GPT) AI model implementation"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4-turbo-preview"  # or "gpt-4o"
        log.info("OpenAI AI model initialized")

    async def get_trading_decision(self, system_prompt: str) -> Dict[str, Any]:
        """Get trading decision from GPT"""
        try:
            # Same user message as Claude
            user_message = """..."""  # (same as above)

            # Call OpenAI API
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1024
            )

            # Extract response
            response_text = completion.choices[0].message.content

            log.info(f"OpenAI response received: {len(response_text)} chars")
            log.debug(f"Raw response: {response_text}")

            return response_text

        except Exception as e:
            log.error(f"Error calling OpenAI API: {e}")
            raise
```

---

## Factory Pattern

### File: `src/ai/__init__.py`

```python
from src.ai.base_model import BaseAIModel
from src.ai.claude_model import ClaudeModel
from src.ai.openai_model import OpenAIModel
from src.config import settings

def get_ai_model() -> BaseAIModel:
    """Factory function to get configured AI model"""
    if settings.ai_model == "claude":
        return ClaudeModel()
    elif settings.ai_model == "openai":
        return OpenAIModel()
    else:
        raise ValueError(f"Unknown AI model: {settings.ai_model}")
```

---

## Usage

```python
from src.ai import get_ai_model
from src.ai.prompt_builder import PromptBuilder

# Initialize
ai_model = get_ai_model()
prompt_builder = PromptBuilder()

# Build prompt
system_prompt = prompt_builder.build_prompt(market_data, portfolio, positions)

# Get decision from AI
raw_response = await ai_model.get_trading_decision(system_prompt)

# Parse response (next task)
decision = parse_ai_response(raw_response)

print(f"Decision: {decision['action']} {decision['symbol']}")
```

---

## Configuration

Switch models in `.env`:

```bash
# Use Claude (default)
AI_MODEL=claude
ANTHROPIC_API_KEY=sk-ant-...

# Use OpenAI
AI_MODEL=openai
OPENAI_API_KEY=sk-...
```

---

## Error Handling

```python
try:
    response = await ai_model.get_trading_decision(prompt)
except anthropic.APIError as e:
    log.error(f"Claude API error: {e}")
    # Fall back to HOLD decision
    return {"action": "HOLD", ...}
except openai.APIError as e:
    log.error(f"OpenAI API error: {e}")
    return {"action": "HOLD", ...}
```

---

## Cost Estimation

**Claude Sonnet:**
- Input: ~$3 per 1M tokens
- Output: ~$15 per 1M tokens
- Per request (~3k tokens in, ~500 out): ~$0.015

**GPT-4 Turbo:**
- Input: ~$10 per 1M tokens
- Output: ~$30 per 1M tokens
- Per request: ~$0.045

**Daily cost (480 runs):**
- Claude: ~$7/day
- GPT-4: ~$22/day

---

## Testing

```python
async def test_ai_model():
    ai_model = get_ai_model()

    # Simple test prompt
    test_prompt = """BTC price: $111,000
    RSI: 56 (neutral)
    MACD: Bullish crossover
    Account balance: $10,000"""

    response = await ai_model.get_trading_decision(test_prompt)

    assert response is not None
    assert len(response) > 0

    print(f"✓ AI model works! Response: {response[:100]}...")
```

---

## Next Steps

→ [Task 11: AI Response Parser](11_ai_parser.md)
