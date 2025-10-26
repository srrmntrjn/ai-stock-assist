"""Utilities for building LLM system prompts from market data."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Iterable, List

from src.config import settings


class PromptBuilder:
    """Build a structured system prompt for the AI model."""

    def __init__(self, invocation_count: int = 0) -> None:
        self.invocation_count = invocation_count

    def build_prompt(
        self,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        positions: Iterable[Any],
    ) -> str:
        """Return a formatted system prompt."""

        sections: List[str] = [self._build_header()]

        for symbol in settings.symbol_list:
            sections.append(self._build_symbol_block(symbol, market_data.get(symbol, {})))

        sections.append(self._build_portfolio_block(portfolio_state, positions))
        return "\n\n".join(filter(None, sections))

    def _build_header(self) -> str:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return (
            f"It has been {self.invocation_count} invocations since you started trading.\n"
            f"The current time is {now}.\n\n"
            "Below, we are providing you with a variety of state data, price data, and predictive signals.\n\n"
            "ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST\n\n"
            "CURRENT MARKET STATE FOR ALL COINS"
        )

    def _build_symbol_block(self, symbol: str, data: Dict[str, Any]) -> str:
        coin = symbol.replace("-PERPETUAL", "")
        intraday = data.get("intraday", {})
        longer_term = data.get("longer_term", {})

        return (
            f"ALL {coin} DATA\n"
            f"current_price = {intraday.get('current_price')}\n"
            f"current_ema20 = {intraday.get('current_ema20')}\n"
            f"current_macd = {intraday.get('current_macd')}\n"
            f"current_rsi (7 period) = {intraday.get('current_rsi_7')}\n\n"
            f"Open Interest: Latest: {data.get('open_interest')} Average: {data.get('open_interest_avg')}\n"
            f"Funding Rate: {data.get('funding_rate')}\n\n"
            "Intraday series (3-minute intervals, oldest → latest):\n"
            f"Mid prices: {intraday.get('prices')}\n"
            f"EMA indicators (20-period): {intraday.get('ema_20')}\n"
            f"MACD indicators: {intraday.get('macd_series')}\n"
            f"RSI indicators (7-Period): {intraday.get('rsi_7_series')}\n"
            f"RSI indicators (14-Period): {intraday.get('rsi_14_series')}\n\n"
            "Longer-term context (4-hour timeframe):\n"
            f"20-Period EMA: {longer_term.get('ema_20')} vs. 50-Period EMA: {longer_term.get('ema_50')}\n"
            f"3-Period ATR: {longer_term.get('atr_3')} vs. 14-Period ATR: {longer_term.get('atr_14')}\n"
            f"Current Volume: {longer_term.get('current_volume')} vs. Average Volume: {longer_term.get('avg_volume')}\n"
            f"MACD indicators: {longer_term.get('macd_series')}\n"
            f"RSI indicators (14-Period): {longer_term.get('rsi_14_series')}"
        )

    def _build_portfolio_block(self, portfolio: Dict[str, Any], positions: Iterable[Any]) -> str:
        formatted_positions = []
        for position in positions:
            formatted_positions.append(
                {
                    "symbol": getattr(position, "symbol", None),
                    "quantity": getattr(position, "quantity", None),
                    "entry_price": getattr(position, "entry_price", None),
                    "current_price": getattr(position, "current_price", None),
                    "liquidation_price": getattr(position, "liquidation_price", None),
                    "unrealized_pnl": getattr(position, "unrealized_pnl", None),
                    "leverage": getattr(position, "leverage", None),
                }
            )

        return (
            "HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE\n"
            f"Current Total Return (percent): {portfolio.get('total_return_pct')}%\n"
            f"Available Cash: {portfolio.get('available_cash')}\n"
            f"Current Account Value: {portfolio.get('account_value')}\n"
            f"Current live positions & performance: {json.dumps(formatted_positions, indent=2)}\n"
            f"Sharpe Ratio: {portfolio.get('sharpe_ratio')}"
        )


__all__ = ["PromptBuilder"]
