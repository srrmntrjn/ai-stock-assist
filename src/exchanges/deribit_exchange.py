"""Deribit exchange implementation using ccxt"""

import ccxt
from typing import List, Optional
from datetime import datetime
from src.exchanges.base import (
    BaseExchange,
    OHLCV,
    OrderBook,
    Position,
    Order,
    Balance
)
from src.logger import log


class DeribitExchange(BaseExchange):
    """Deribit exchange implementation"""

    def __init__(self, api_key: str, secret: str, testnet: bool = True):
        super().__init__(api_key, secret, testnet)

        # Initialize ccxt Deribit client
        self.exchange = ccxt.deribit({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
        })

        # Set testnet if needed
        if testnet:
            self.exchange.set_sandbox_mode(True)
            log.info("Deribit exchange initialized in TESTNET mode")
        else:
            log.info("Deribit exchange initialized in PRODUCTION mode")

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to Deribit format
        Examples: BTC-PERPETUAL, ETH-PERPETUAL
        """
        if symbol.endswith("-PERPETUAL"):
            return symbol
        # If just "BTC", "ETH", etc., add -PERPETUAL
        return f"{symbol}-PERPETUAL"

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "3m",
        limit: int = 100
    ) -> List[OHLCV]:
        """
        Fetch OHLCV candle data

        Args:
            symbol: Trading pair (e.g., "BTC-PERPETUAL")
            timeframe: Candle timeframe (1m, 3m, 5m, 15m, 1h, 4h, etc.)
            limit: Number of candles to fetch
        """
        try:
            symbol = self.normalize_symbol(symbol)

            # Fetch OHLCV data
            ohlcv_data = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit
            )

            # Convert to OHLCV objects
            candles = []
            for candle in ohlcv_data:
                timestamp, open_, high, low, close, volume = candle
                candles.append(OHLCV(
                    timestamp=datetime.fromtimestamp(timestamp / 1000),
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume
                ))

            log.debug(f"Fetched {len(candles)} candles for {symbol} ({timeframe})")
            return candles

        except Exception as e:
            log.error(f"Error fetching OHLCV for {symbol}: {e}")
            raise

    async def get_open_interest(self, symbol: str) -> float:
        """Get current open interest for a perpetual future"""
        try:
            symbol = self.normalize_symbol(symbol)
            ticker = self.exchange.fetch_ticker(symbol)

            # Deribit provides open interest in the ticker
            open_interest = ticker.get('info', {}).get('open_interest', 0)

            log.debug(f"Open Interest for {symbol}: {open_interest}")
            return float(open_interest)

        except Exception as e:
            log.error(f"Error fetching open interest for {symbol}: {e}")
            return 0.0

    async def get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate for a perpetual future"""
        try:
            symbol = self.normalize_symbol(symbol)
            ticker = self.exchange.fetch_ticker(symbol)

            # Deribit provides funding rate in the ticker
            funding_rate = ticker.get('info', {}).get('funding_8h', 0)

            log.debug(f"Funding Rate for {symbol}: {funding_rate}")
            return float(funding_rate)

        except Exception as e:
            log.error(f"Error fetching funding rate for {symbol}: {e}")
            return 0.0

    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        """Get order book snapshot"""
        try:
            symbol = self.normalize_symbol(symbol)
            order_book = self.exchange.fetch_order_book(symbol, limit=depth)

            return OrderBook(
                timestamp=datetime.now(),
                bids=order_book['bids'],
                asks=order_book['asks']
            )

        except Exception as e:
            log.error(f"Error fetching order book for {symbol}: {e}")
            raise

    async def get_balance(self) -> Balance:
        """Get account balance"""
        try:
            balance_data = self.exchange.fetch_balance()

            # Deribit uses USD as the quote currency
            total = balance_data.get('total', {}).get('USD', 0)
            free = balance_data.get('free', {}).get('USD', 0)
            used = balance_data.get('used', {}).get('USD', 0)

            return Balance(
                total=float(total),
                available=float(free),
                in_positions=float(used)
            )

        except Exception as e:
            log.error(f"Error fetching balance: {e}")
            raise

    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        try:
            positions_data = self.exchange.fetch_positions()
            positions = []

            for pos in positions_data:
                if pos['contracts'] > 0:  # Only include open positions
                    positions.append(Position(
                        symbol=pos['symbol'],
                        side='long' if pos['side'] == 'long' else 'short',
                        quantity=float(pos['contracts']),
                        entry_price=float(pos['entryPrice']),
                        current_price=float(pos['markPrice']),
                        unrealized_pnl=float(pos['unrealizedPnl']),
                        liquidation_price=float(pos.get('liquidationPrice', 0)),
                        leverage=int(pos.get('leverage', 1))
                    ))

            log.debug(f"Found {len(positions)} open positions")
            return positions

        except Exception as e:
            log.error(f"Error fetching positions: {e}")
            return []

    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Order:
        """Place a market order"""
        try:
            symbol = self.normalize_symbol(symbol)

            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=quantity
            )

            log.info(f"Market {side} order placed: {symbol} {quantity} contracts")

            return Order(
                order_id=order['id'],
                symbol=symbol,
                side=side,
                order_type='market',
                quantity=quantity,
                status='filled' if order['status'] == 'closed' else 'pending'
            )

        except Exception as e:
            log.error(f"Error placing market order for {symbol}: {e}")
            raise

    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Order:
        """Place a limit order"""
        try:
            symbol = self.normalize_symbol(symbol)

            order = self.exchange.create_limit_order(
                symbol=symbol,
                side=side,
                amount=quantity,
                price=price
            )

            log.info(f"Limit {side} order placed: {symbol} {quantity} @ {price}")

            return Order(
                order_id=order['id'],
                symbol=symbol,
                side=side,
                order_type='limit',
                quantity=quantity,
                price=price,
                status=order['status']
            )

        except Exception as e:
            log.error(f"Error placing limit order for {symbol}: {e}")
            raise

    async def place_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float
    ) -> Order:
        """Place a stop loss order"""
        try:
            symbol = self.normalize_symbol(symbol)

            # Deribit uses stopLoss parameter
            order = self.exchange.create_order(
                symbol=symbol,
                type='stop_market',
                side=side,
                amount=quantity,
                params={'stopPrice': stop_price}
            )

            log.info(f"Stop loss order placed: {symbol} {quantity} @ {stop_price}")

            return Order(
                order_id=order['id'],
                symbol=symbol,
                side=side,
                order_type='stop_loss',
                quantity=quantity,
                price=stop_price,
                status=order['status']
            )

        except Exception as e:
            log.error(f"Error placing stop loss for {symbol}: {e}")
            raise

    async def place_take_profit(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Order:
        """Place a take profit order"""
        try:
            symbol = self.normalize_symbol(symbol)

            # Deribit uses takeProfit parameter
            order = self.exchange.create_order(
                symbol=symbol,
                type='take_profit_market',
                side=side,
                amount=quantity,
                params={'stopPrice': price}
            )

            log.info(f"Take profit order placed: {symbol} {quantity} @ {price}")

            return Order(
                order_id=order['id'],
                symbol=symbol,
                side=side,
                order_type='take_profit',
                quantity=quantity,
                price=price,
                status=order['status']
            )

        except Exception as e:
            log.error(f"Error placing take profit for {symbol}: {e}")
            raise

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.exchange.cancel_order(order_id)
            log.info(f"Order cancelled: {order_id}")
            return True

        except Exception as e:
            log.error(f"Error cancelling order {order_id}: {e}")
            return False

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol
        Note: Deribit sets leverage at the account level, not per symbol
        """
        try:
            symbol = self.normalize_symbol(symbol)

            # Deribit uses a different API for setting leverage
            # This might need adjustment based on the specific Deribit API
            self.exchange.set_leverage(leverage, symbol)

            log.info(f"Leverage set to {leverage}x for {symbol}")
            return True

        except Exception as e:
            log.warning(f"Note: Deribit may set leverage differently: {e}")
            return False
