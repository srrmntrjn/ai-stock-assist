# Task 16: Main Orchestrator

**Status:** ⏭️ PENDING

**Estimated Time:** 2 hours

---

## Overview

Create the main orchestrator that ties all components together and executes the complete trading loop every 3 minutes.

---

## Implementation Details

### File: `src/main.py`

---

## Trading Loop Flow

```
1. Fetch market data (OHLCV, OI, funding) for all 6 coins
2. Calculate technical indicators (EMA, MACD, RSI, ATR)
3. Get current portfolio state
4. Build AI system prompt
5. Get AI trading decision
6. Parse and validate AI response
7. Execute trade (if action != HOLD)
8. Update positions and portfolio
9. Log everything
10. Sleep until next iteration
```

---

## Class Structure

```python
class TradingBot:
    """Main trading bot orchestrator"""

    def __init__(self):
        # Initialize components
        self.exchange = get_exchange()
        self.ai_model = get_ai_model()
        self.prompt_builder = PromptBuilder()
        self.indicators = TechnicalIndicators()
        self.risk_manager = RiskManager()
        self.portfolio_tracker = PortfolioTracker()

        self.invocation_count = 0
        log.info("Trading bot initialized")

    async def run_iteration(self):
        """Run one trading iteration"""
        self.invocation_count += 1

        log.info(f"=== Iteration #{self.invocation_count} ===")

        try:
            # 1. Fetch market data
            market_data = await self._fetch_market_data()

            # 2. Calculate indicators
            indicators_data = await self._calculate_indicators(market_data)

            # 3. Get portfolio state
            portfolio_state = await self._get_portfolio_state()

            # 4. Build AI prompt
            system_prompt = self.prompt_builder.build_prompt(
                market_data=indicators_data,
                portfolio_state=portfolio_state,
                positions=await self.exchange.get_positions()
            )

            # 5. Get AI decision
            raw_response = await self.ai_model.get_trading_decision(system_prompt)

            # 6. Parse response
            decision = parse_ai_response(raw_response)

            log.info(f"AI Decision: {decision['action']} {decision.get('symbol', 'N/A')} "
                    f"(confidence: {decision.get('confidence', 0):.2f})")

            # 7. Execute trade
            if decision['action'] != 'HOLD':
                await self._execute_trade(decision)

            # 8. Update portfolio
            await self.portfolio_tracker.update()

            # 9. Log performance
            await self._log_performance()

        except Exception as e:
            log.error(f"Error in trading iteration: {e}", exc_info=True)

    async def _fetch_market_data(self) -> Dict[str, Any]:
        """Fetch OHLCV, OI, funding for all symbols"""
        market_data = {}

        for symbol in settings.symbol_list:
            try:
                # Fetch 3-minute candles
                candles_3m = await self.exchange.get_ohlcv(symbol, "3m", 100)

                # Fetch 4-hour candles
                candles_4h = await self.exchange.get_ohlcv(symbol, "4h", 100)

                # Fetch OI and funding
                open_interest = await self.exchange.get_open_interest(symbol)
                funding_rate = await self.exchange.get_funding_rate(symbol)

                market_data[symbol] = {
                    'candles_3m': candles_3m,
                    'candles_4h': candles_4h,
                    'open_interest': open_interest,
                    'funding_rate': funding_rate
                }

                log.debug(f"Fetched data for {symbol}")

            except Exception as e:
                log.error(f"Error fetching data for {symbol}: {e}")

        return market_data

    async def _calculate_indicators(self, market_data: Dict) -> Dict[str, Any]:
        """Calculate technical indicators for all symbols"""
        indicators_data = {}

        for symbol, data in market_data.items():
            try:
                indicators = self.indicators.calculate_all_indicators(
                    candles_3m=data['candles_3m'],
                    candles_4h=data['candles_4h']
                )

                indicators['open_interest'] = data['open_interest']
                indicators['funding_rate'] = data['funding_rate']

                indicators_data[symbol] = indicators

            except Exception as e:
                log.error(f"Error calculating indicators for {symbol}: {e}")

        return indicators_data

    async def _get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state"""
        balance = await self.exchange.get_balance()
        positions = await self.exchange.get_positions()

        # Calculate metrics
        total_pnl = sum(p.unrealized_pnl for p in positions)
        total_return_pct = (balance.total - settings.initial_balance) / settings.initial_balance * 100

        return {
            'available_cash': balance.available,
            'account_value': balance.total,
            'total_return_pct': total_return_pct,
            'sharpe_ratio': await self.portfolio_tracker.get_sharpe_ratio(),
            'num_positions': len(positions)
        }

    async def _execute_trade(self, decision: Dict[str, Any]):
        """Execute trade based on AI decision"""
        if not settings.enable_trading:
            log.warning("Trading disabled in config, skipping execution")
            return

        try:
            # Validate with risk manager
            if not self.risk_manager.validate_trade(decision):
                log.warning("Trade rejected by risk manager")
                return

            symbol = decision['symbol']
            action = decision['action']
            position_size_pct = decision.get('position_size_pct', settings.position_size_pct)

            # Calculate quantity
            balance = await self.exchange.get_balance()
            position_value = balance.available * (position_size_pct / 100)

            current_price = (await self.exchange.get_ohlcv(symbol, "3m", 1))[0].close
            quantity = position_value / current_price

            # Execute market order
            if action == 'BUY':
                order = await self.exchange.place_market_order(symbol, 'buy', quantity)
            elif action == 'SELL':
                order = await self.exchange.place_market_order(symbol, 'sell', quantity)

            log.info(f"Trade executed: {order}")

            # Place stop loss and take profit
            if decision.get('stop_loss'):
                await self.exchange.place_stop_loss(
                    symbol,
                    'sell' if action == 'BUY' else 'buy',
                    quantity,
                    decision['stop_loss']
                )

            if decision.get('take_profit'):
                await self.exchange.place_take_profit(
                    symbol,
                    'sell' if action == 'BUY' else 'buy',
                    quantity,
                    decision['take_profit']
                )

        except Exception as e:
            log.error(f"Error executing trade: {e}", exc_info=True)

    async def _log_performance(self):
        """Log current performance metrics"""
        balance = await self.exchange.get_balance()
        positions = await self.exchange.get_positions()

        total_return = (balance.total - settings.initial_balance) / settings.initial_balance * 100

        log.info(f"Portfolio Value: ${balance.total:.2f} | "
                f"Return: {total_return:.2f}% | "
                f"Positions: {len(positions)}")

    async def start(self):
        """Start the trading bot (called by scheduler)"""
        log.info("🚀 Trading bot started")

        # Run first iteration immediately
        await self.run_iteration()

        log.info("Iteration complete")


# Entry point
async def main():
    """Main entry point"""
    # Validate configuration
    settings.validate_config()

    # Create bot
    bot = TradingBot()

    # Run one iteration (scheduler will handle repeated runs)
    await bot.start()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Error Handling Strategy

1. **API Failures:** Log and skip iteration
2. **Data Fetch Errors:** Skip that symbol, continue with others
3. **AI Errors:** Default to HOLD
4. **Trade Execution Errors:** Log, alert, don't crash

---

## Testing

```bash
# Run one iteration
python src/main.py

# Check logs
tail -f logs/trading_bot.log
```

---

## Next Steps

→ [Task 15: Scheduler](15_scheduler.md) - Automate iterations every 3 minutes
→ [Task 17: End-to-End Testing](17_testing.md)
