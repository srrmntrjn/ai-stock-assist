"""Parse AI model responses into validated trading decisions."""

from __future__ import annotations

import json
from typing import Any, Dict

from src.logger import log


REQUIRED_FIELDS = {"symbol", "action"}
VALID_ACTIONS = {"BUY", "SELL", "HOLD"}


def parse_ai_response(response: Any) -> Dict[str, Any]:
    """Parse the raw response from the AI model.

    The AI integration is still in progress, so this parser is intentionally
    permissive. It accepts dictionaries or JSON encoded strings and ensures the
    minimum required fields are present. Missing optional fields are filled with
    sensible defaults.
    """

    if isinstance(response, dict):
        data = response
    else:
        try:
            data = json.loads(str(response))
        except json.JSONDecodeError:
            log.warning("Failed to decode AI response, defaulting to HOLD decision")
            data = {}

    # Normalise keys
    normalized = {str(k).lower(): v for k, v in data.items()}

    action = str(normalized.get("action", "HOLD")).upper()
    if action not in VALID_ACTIONS:
        log.warning("Invalid AI action '%s', defaulting to HOLD", action)
        action = "HOLD"

    symbol = normalized.get("symbol")
    if not symbol:
        symbol = "BTC-PERPETUAL"

    result: Dict[str, Any] = {
        "symbol": symbol,
        "action": action,
        "confidence": float(normalized.get("confidence", 0.0) or 0.0),
        "reasoning": normalized.get("reasoning", "No reasoning provided."),
        "entry_type": str(normalized.get("entry_type", "MARKET")).upper(),
        "entry_price": normalized.get("entry_price"),
        "stop_loss": normalized.get("stop_loss"),
        "take_profit": normalized.get("take_profit"),
        "position_size_pct": float(normalized.get("position_size_pct", 0.0) or 0.0),
    }

    if result["position_size_pct"] <= 0:
        result["position_size_pct"] = 0.0

    return result


__all__ = ["parse_ai_response"]
