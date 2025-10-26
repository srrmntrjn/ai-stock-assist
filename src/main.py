"""Main entry point for running a single trading iteration."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from src.ai import get_ai_model
from src.ai.prompt_builder import PromptBuilder
from src.ai.response_parser import parse_ai_response
from src.config import settings
from src.analytics.indicators import TechnicalIndicators
from src.exchanges import get_exchange
from src.exchanges.base import Balance, Position
from src.logger import log
from src.portfolio.tracker import PortfolioTracker
from src.trading.risk_manager import RiskManager


class TradingBot:
    """Main trading bot orchestrator."""

    def __init__(self) -> None:
        self.exchange = get_exchange()
        self.ai_model = get_ai_model()
        self.prompt_builder = PromptBuilder()
        self.indicators = TechnicalIndicators()
        self.risk_manager = RiskManager()
        self.portfolio_tracker = PortfolioTracker()
        self.invocation_count = 0

        log.info("Trading bot initialized")

    async def run_iteration(self) -> None:
        """Run a single trading loop iteration."""

        self.invocation_count += 1
        self.prompt_builder.invocation_count = self.invocation_count
        log.info("=== Iteration #%s ===", self.invocation_count)

        try:
            market_data = await self._fetch_market_data()
            indicator_data = await self._calculate_indicators(market_data)
            portfolio_state, balance, positions = await self._get_portfolio_state()

            system_prompt = self.prompt_builder.build_prompt(
                market_data=indicator_data,
                portfolio_state=portfolio_state,
                positions=positions,
            )

            raw_response = await self.ai_model.get_trading_decision(system_prompt)
            decision = parse_ai_response(raw_response)

            log.info(
                "AI Decision: %s %s (confidence %.2f)",
                decision.get("action"),
                decision.get("symbol"),
                decision.get("confidence", 0.0),
            )

            if decision.get("action") != "HOLD":
                await self._execute_trade(decision, balance)
                # Refresh balance/positions after potential trade execution
                balance = await self.exchange.get_balance()
                positions = await self.exchange.get_positions()
                sharpe_ratio = await self.portfolio_tracker.get_sharpe_ratio()
                portfolio_state = self._build_portfolio_state(
                    balance,
                    positions,
                    sharpe_ratio,
                )

            await self.portfolio_tracker.update(balance, positions)
            await self._log_performance(balance, positions)

        except Exception as exc:  # pragma: no cover - defensive logging
            log.error("Error in trading iteration: %s", exc, exc_info=True)

    async def _fetch_market_data(self) -> Dict[str, Any]:
        """Fetch OHLCV, open interest and funding rate for all symbols."""

        market_data: Dict[str, Any] = {}
        for symbol in settings.symbol_list:
            try:
                candles_3m = await self.exchange.get_ohlcv(symbol, "3m", 120)
                candles_4h = await self.exchange.get_ohlcv(symbol, "4h", 120)
                open_interest = await self.exchange.get_open_interest(symbol)
                funding_rate = await self.exchange.get_funding_rate(symbol)

                market_data[symbol] = {
                    "candles_3m": candles_3m,
                    "candles_4h": candles_4h,
                    "open_interest": open_interest,
                    "funding_rate": funding_rate,
                }
            except Exception as exc:
                log.error("Failed to fetch market data for %s: %s", symbol, exc, exc_info=True)

        if not market_data:
            raise RuntimeError("No market data available for any symbol")

        return market_data

    async def _calculate_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for symbol, data in market_data.items():
            try:
                calculated = self.indicators.calculate(
                    candles_3m=data.get("candles_3m", []),
                    candles_4h=data.get("candles_4h", []),
                )
                calculated["open_interest"] = data.get("open_interest")
                calculated["open_interest_avg"] = data.get("open_interest")
                calculated["funding_rate"] = data.get("funding_rate")
                results[symbol] = calculated
            except Exception as exc:
                log.error("Failed to calculate indicators for %s: %s", symbol, exc, exc_info=True)

        return results

    async def _get_portfolio_state(self) -> tuple[Dict[str, Any], Balance, List[Position]]:
        balance = await self.exchange.get_balance()
        positions = await self.exchange.get_positions()
        sharpe_ratio = await self.portfolio_tracker.get_sharpe_ratio()
        portfolio_state = self._build_portfolio_state(balance, positions, sharpe_ratio)
        return portfolio_state, balance, positions

    def _build_portfolio_state(
        self,
        balance: Balance,
        positions: List[Position],
        sharpe_ratio: float,
    ) -> Dict[str, Any]:
        total_return_pct = 0.0
        if settings.initial_balance > 0:
            total_return_pct = (
                (balance.total - settings.initial_balance) / settings.initial_balance * 100
            )

        return {
            "available_cash": balance.available,
            "account_value": balance.total,
            "total_return_pct": round(total_return_pct, 4),
            "sharpe_ratio": sharpe_ratio,
            "num_positions": len(positions),
        }

    async def _execute_trade(self, decision: Dict[str, Any], balance: Balance) -> None:
        if not settings.enable_trading:
            log.warning("Trading disabled in configuration, skipping execution")
            return

        if not self.risk_manager.validate_trade(decision):
            return

        symbol = decision.get("symbol")
        action = decision.get("action", "HOLD").upper()

        if action not in {"BUY", "SELL"}:
            log.warning("Unsupported trade action: %s", action)
            return
        position_size_pct = decision.get("position_size_pct") or settings.position_size_pct

        try:
            candles = await self.exchange.get_ohlcv(symbol, "3m", 1)
            if not candles:
                log.warning("No recent candles available for %s", symbol)
                return

            current_price = candles[-1].close
            if current_price <= 0:
                log.warning("Invalid current price for %s", symbol)
                return

            available_cash = balance.available
            position_value = available_cash * (position_size_pct / 100)
            quantity = position_value / current_price

            if quantity <= 0:
                log.warning("Calculated quantity %.4f for %s is not tradeable", quantity, symbol)
                return

            side = "buy" if action == "BUY" else "sell"
            order = await self.exchange.place_market_order(symbol, side, quantity)
            log.info("Trade executed: %s", order)

            stop_loss = decision.get("stop_loss")
            take_profit = decision.get("take_profit")

            if stop_loss:
                await self.exchange.place_stop_loss(
                    symbol,
                    "sell" if action == "BUY" else "buy",
                    quantity,
                    stop_loss,
                )

            if take_profit:
                await self.exchange.place_take_profit(
                    symbol,
                    "sell" if action == "BUY" else "buy",
                    quantity,
                    take_profit,
                )

        except Exception as exc:
            log.error("Error executing trade for %s: %s", symbol, exc, exc_info=True)

    async def _log_performance(self, balance: Balance, positions: List[Position]) -> None:
        sharpe = await self.portfolio_tracker.get_sharpe_ratio()
        total_return = 0.0
        if settings.initial_balance > 0:
            total_return = (
                (balance.total - settings.initial_balance) / settings.initial_balance * 100
            )

        log.info(
            "Portfolio Value: $%.2f | Return: %.2f%% | Positions: %s | Sharpe: %.4f",
            balance.total,
            total_return,
            len(positions),
            sharpe,
        )

    async def start(self) -> None:
        log.info("🚀 Trading bot started")
        await self.run_iteration()
        log.info("Iteration complete")


async def main() -> None:
    """Application entry point."""

    try:
        settings.validate_config()
    except ValueError as exc:
        log.warning("Configuration validation warning: %s", exc)

    bot = TradingBot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
