"""Simple Flask dashboard for monitoring trading progress."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template

from src.config import settings
from src.exchanges.mock_exchange import MockExchange

app = Flask(__name__, template_folder="templates", static_folder="static")

# Create a single exchange instance so that we reuse cached market data and
# avoid hitting the filesystem on every request.
_exchange: MockExchange | None = None


def get_exchange() -> MockExchange:
    """Return a cached instance of the mock exchange."""
    global _exchange
    if _exchange is None:
        _exchange = MockExchange(
            api_key=settings.exchange_api_key,
            secret=settings.exchange_secret,
            testnet=settings.environment == "testnet",
        )
    return _exchange


def _load_state() -> Dict[str, Any]:
    state_file = Path("data/mock_exchange_state.json")
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text())
    except json.JSONDecodeError:
        return {}


def _serialize_positions(positions: List[Any]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for position in positions:
        position_dict = asdict(position)
        # Format floats for readability on the frontend.
        position_dict.update(
            {
                "quantity": float(position_dict.get("quantity", 0.0)),
                "entry_price": float(position_dict.get("entry_price", 0.0)),
                "current_price": float(position_dict.get("current_price", 0.0)),
                "unrealized_pnl": float(position_dict.get("unrealized_pnl", 0.0)),
                "liquidation_price": (
                    float(position_dict.get("liquidation_price"))
                    if position_dict.get("liquidation_price") is not None
                    else None
                ),
            }
        )
        serialized.append(position_dict)
    return serialized


def _build_balance_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    balance = state.get("balance", {})
    total = float(balance.get("total", settings.initial_balance))
    available = float(balance.get("available", 0.0))
    in_positions = float(balance.get("in_positions", 0.0))
    profit_loss = total - settings.initial_balance
    profit_loss_pct = (
        (profit_loss / settings.initial_balance) * 100
        if settings.initial_balance
        else 0.0
    )

    return {
        "total": total,
        "available": available,
        "in_positions": in_positions,
        "profit_loss": profit_loss,
        "profit_loss_pct": profit_loss_pct,
    }


def _build_balance_history(state: Dict[str, Any], total_balance: float) -> List[Dict[str, Any]]:
    history = state.get("balance_history") or []
    if not history:
        # If we don't have a history recorded yet, synthesise a basic timeline
        # using the initial balance and the most recent total balance so the
        # chart has something meaningful to display.
        start_time = None
        if state.get("trade_history"):
            try:
                start_time = datetime.fromisoformat(state["trade_history"][0]["timestamp"])
            except (KeyError, ValueError, IndexError):
                start_time = None
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=1)
        history = [
            {
                "timestamp": (start_time - timedelta(minutes=1)).isoformat(),
                "total": settings.initial_balance,
            },
            {
                "timestamp": datetime.now().isoformat(),
                "total": total_balance,
            },
        ]
    else:
        # Ensure floats for frontend
        for item in history:
            item["total"] = float(item.get("total", total_balance))
    return history


def get_dashboard_data() -> Dict[str, Any]:
    state = _load_state()
    exchange = get_exchange()

    try:
        balance = asyncio.run(exchange.get_balance())
    except RuntimeError:
        # "asyncio.run" cannot be called from a running event loop; fall back
        # to creating a new loop manually. This primarily happens when the
        # server is run in debug mode with reloader threads.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        balance = loop.run_until_complete(exchange.get_balance())
        loop.close()
    balance_dict = asdict(balance)

    try:
        positions = asyncio.run(exchange.get_positions())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        positions = loop.run_until_complete(exchange.get_positions())
        loop.close()

    serialized_positions = _serialize_positions(positions)
    balance_summary = _build_balance_summary(state)
    balance_history = _build_balance_history(state, balance_summary["total"])

    orders = []
    for order_id, info in state.get("orders", {}).items():
        order = {"order_id": order_id, **info}
        orders.append(order)
    orders.sort(key=lambda item: item.get("status", ""))

    trade_history = list(state.get("trade_history", []))
    trade_history.sort(key=lambda item: item.get("timestamp", ""), reverse=True)

    return {
        "balance": balance_summary,
        "balance_history": balance_history,
        "positions": serialized_positions,
        "open_orders": orders,
        "trade_history": trade_history[:100],
        "last_updated": datetime.now().isoformat(),
        "raw_balance": balance_dict,
    }


@app.route("/")
def index():
    data = get_dashboard_data()
    return render_template("index.html", initial_data=json.dumps(data))


@app.route("/api/dashboard")
def api_dashboard():
    data = get_dashboard_data()
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
