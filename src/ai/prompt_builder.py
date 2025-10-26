"""System prompt builder for AI trading analysis."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Iterable, List

from src.config import settings
from src.exchanges.base import Position


class PromptBuilder:
    """Builds AI system prompts from market data."""

    def __init__(self, invocation_count: int = 0) -> None:
        self.invocation_count = invocation_count

    def build_prompt(
        self,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        positions: List[Position],
    ) -> str:
        """Build the complete system prompt for the AI model."""

        prompt_parts: List[str] = []
        prompt_parts.append(self._build_header())

        for symbol in settings.symbol_list:
            coin_data = market_data.get(symbol, {})
            prompt_parts.append(self._build_coin_section(symbol, coin_data))

        prompt_parts.append(self._build_portfolio_section(portfolio_state, positions))
        return "\n\n".join(prompt_parts)

    def _build_header(self) -> str:
        """Construct the header section of the prompt."""

        current_time = datetime.now().isoformat()
        return (
            f"It has been {self.invocation_count} invocations since you started trading.\n"
            f"The current time is {current_time}.\n\n"
            "Below, we are providing you with a variety of state data, price data, and predictive signals.\n\n"
            "ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST\n\n"
            "CURRENT MARKET STATE FOR ALL COINS"
        )

    def _build_coin_section(self, symbol: str, data: Dict[str, Any]) -> str:
        """Construct the market data section for a single coin."""

        coin = symbol.replace("-PERPETUAL", "")
        intraday: Dict[str, Any] = data.get("intraday", {}) or {}
        longer_term: Dict[str, Any] = data.get("longer_term", {}) or {}

        return (
            f"ALL {coin} DATA\n"
            f"current_price = {self._format_value(intraday.get('current_price'))}, "
            f"current_ema20 = {self._format_value(intraday.get('current_ema20'))}, "
            f"current_macd = {self._format_value(intraday.get('current_macd'))}, "
            f"current_rsi (7 period) = {self._format_value(intraday.get('current_rsi_7'))}\n\n"
            f"Open Interest: Latest: {self._format_value(data.get('open_interest'))} "
            f"Average: {self._format_value(data.get('open_interest_avg'))}\n"
            f"Funding Rate: {self._format_value(data.get('funding_rate'))}\n\n"
            "Intraday series (3-minute intervals, oldest → latest):\n"
            f"Mid prices: {self._format_series(intraday.get('prices'))}\n"
            f"EMA indicators (20-period): {self._format_series(intraday.get('ema_20'))}\n"
            f"MACD indicators: {self._format_series(intraday.get('macd'))}\n"
            f"RSI indicators (7-Period): {self._format_series(intraday.get('rsi_7'))}\n"
            f"RSI indicators (14-Period): {self._format_series(intraday.get('rsi_14'))}\n\n"
            "Longer-term context (4-hour timeframe):\n"
            f"20-Period EMA: {self._format_value(longer_term.get('ema_20'))} vs. "
            f"50-Period EMA: {self._format_value(longer_term.get('ema_50'))}\n"
            f"3-Period ATR: {self._format_value(longer_term.get('atr_3'))} vs. "
            f"14-Period ATR: {self._format_value(longer_term.get('atr_14'))}\n"
            f"Current Volume: {self._format_value(longer_term.get('current_volume'))} vs. "
            f"Average Volume: {self._format_value(longer_term.get('avg_volume'))}\n"
            f"MACD indicators: {self._format_series(longer_term.get('macd'))}\n"
            f"RSI indicators (14-Period): {self._format_series(longer_term.get('rsi_14'))}"
        )

    def _build_portfolio_section(
        self,
        portfolio: Dict[str, Any],
        positions: List[Position],
    ) -> str:
        """Construct the portfolio performance section."""

        positions_formatted = [
            {
                "symbol": position.symbol,
                "side": position.side,
                "quantity": position.quantity,
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "liquidation_price": position.liquidation_price,
                "unrealized_pnl": position.unrealized_pnl,
                "leverage": position.leverage,
            }
            for position in positions
        ]

        positions_json = json.dumps(positions_formatted, indent=2)

        return (
            "HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE\n"
            f"Current Total Return (percent): {self._format_value(portfolio.get('total_return_pct'))}%\n"
            f"Available Cash: {self._format_value(portfolio.get('available_cash'))}\n"
            f"Current Account Value: {self._format_value(portfolio.get('account_value'))}\n"
            f"Current live positions & performance: {positions_json}\n"
            f"Sharpe Ratio: {self._format_value(portfolio.get('sharpe_ratio'))}"
        )

    @staticmethod
    def _format_value(value: Any) -> Any:
        """Return a placeholder when a value is missing."""

        return "N/A" if value is None else value

    @staticmethod
    def _format_series(series: Any) -> str:
        """Format a sequence for display in the prompt."""

        if isinstance(series, Iterable) and not isinstance(series, (str, bytes, dict)):
            return json.dumps(list(series))
        return json.dumps([]) if series is None else json.dumps(series)


__all__ = ["PromptBuilder"]
