"""Mock exchange simulator that mimics Coinbase API for testing"""

import json
import uuid
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from src.exchanges.base import (
    BaseExchange,
    OHLCV,
    OrderBook,
    Position,
    Order,
    Balance
)
from src.exchanges.data_fetcher import MarketDataFetcher
from src.logger import log
from src.config import settings


class MockExchange(BaseExchange):
    """
    Mock exchange that simulates Coinbase Financial Markets API
    - Fetches REAL market data from free APIs
    - Simulates order execution locally
    - Tracks positions, PnL, and portfolio state
    - Same interface as real exchange for seamless production cutover
    """

    def __init__(self, api_key: str = "", secret: str = "", testnet: bool = True):
        super().__init__(api_key, secret, testnet)

        self.data_fetcher = MarketDataFetcher()
        self.state_file = Path("data/mock_exchange_state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Load or initialize state
        self.state = self._load_state()

        log.info(f"MockExchange initialized - Balance: ${self.state['balance']['total']:.2f}")

    def _load_state(self) -> dict:
        """Load state from disk or initialize"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                log.info("Loaded existing mock exchange state")
                return state

        # Initialize new state
        initial_state = {
            'balance': {
                'total': settings.initial_balance,
                'available': settings.initial_balance,
                'in_positions': 0.0
            },
            'positions': {},  # symbol -> position data
            'orders': {},     # order_id -> order data
            'trade_history': []
        }

        self._save_state(initial_state)
        log.info(f"Initialized new mock exchange with ${settings.initial_balance} balance")
        return initial_state

    def _save_state(self, state: Optional[dict] = None):
        """Save state to disk"""
        if state is None:
            state = self.state

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format"""
        if not symbol.endswith("-PERPETUAL"):
            return f"{symbol}-PERPETUAL"
        return symbol

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "3m",
        limit: int = 100
    ) -> List[OHLCV]:
        """Fetch OHLCV from free APIs"""
        symbol = self.normalize_symbol(symbol)

        # Convert timeframe to minutes
        if timeframe == "3m":
            minutes = 3
        elif timeframe == "4h":
            minutes = 240
        else:
            minutes = int(timeframe.replace('m', '').replace('h', '')) * (60 if 'h' in timeframe else 1)

        # Fetch from CoinGecko
        ohlcv_data = self.data_fetcher.get_ohlcv(symbol, timeframe_minutes=minutes, limit=limit)

        # Convert to OHLCV objects
        candles = []
        for candle in ohlcv_data:
            candles.append(OHLCV(
                timestamp=datetime.fromtimestamp(candle['timestamp'] / 1000),
                open=candle['open'],
                high=candle['high'],
                low=candle['low'],
                close=candle['close'],
                volume=candle['volume']
            ))

        return candles

    async def get_open_interest(self, symbol: str) -> float:
        """Get estimated open interest"""
        symbol = self.normalize_symbol(symbol)
        return self.data_fetcher.estimate_open_interest(symbol)

    async def get_funding_rate(self, symbol: str) -> float:
        """Get estimated funding rate"""
        symbol = self.normalize_symbol(symbol)
        return self.data_fetcher.estimate_funding_rate(symbol)

    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        """Simulate order book"""
        symbol = self.normalize_symbol(symbol)
        current_price = self.data_fetcher.get_current_price(symbol)

        # Generate synthetic order book
        bids = []
        asks = []
        for i in range(depth):
            bid_price = current_price * (1 - (i + 1) * 0.0001)
            ask_price = current_price * (1 + (i + 1) * 0.0001)
            size = 100.0 / (i + 1)  # Decreasing size

            bids.append((bid_price, size))
            asks.append((ask_price, size))

        return OrderBook(
            timestamp=datetime.now(),
            bids=bids,
            asks=asks
        )

    async def get_balance(self) -> Balance:
        """Get account balance"""
        return Balance(
            total=self.state['balance']['total'],
            available=self.state['balance']['available'],
            in_positions=self.state['balance']['in_positions']
        )

    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        positions = []

        for symbol, pos_data in self.state['positions'].items():
            # Get current price
            current_price = self.data_fetcher.get_current_price(symbol)

            # Calculate PnL
            entry_price = pos_data['entry_price']
            quantity = pos_data['quantity']
            leverage = pos_data['leverage']
            side = pos_data['side']

            if side == 'long':
                pnl = (current_price - entry_price) * quantity * leverage
            else:  # short
                pnl = (entry_price - current_price) * quantity * leverage

            # Calculate liquidation price
            if side == 'long':
                liq_price = entry_price * (1 - 1 / (leverage * 1.5))
            else:
                liq_price = entry_price * (1 + 1 / (leverage * 1.5))

            positions.append(Position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                current_price=current_price,
                unrealized_pnl=pnl,
                liquidation_price=liq_price,
                leverage=leverage
            ))

        return positions

    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Order:
        """Simulate market order execution"""
        symbol = self.normalize_symbol(symbol)
        order_id = str(uuid.uuid4())

        # Get current market price
        current_price = self.data_fetcher.get_current_price(symbol)

        # Simulate slippage (0.05%)
        fill_price = current_price * (1.0005 if side == 'buy' else 0.9995)

        # Create order
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type='market',
            quantity=quantity,
            price=fill_price,
            status='filled'
        )

        # Update position
        await self._update_position(symbol, side, quantity, fill_price)

        # Log trade
        self.state['trade_history'].append({
            'timestamp': datetime.now().isoformat(),
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': fill_price,
            'type': 'market'
        })

        self._save_state()

        log.info(f"[MOCK] Market {side} filled: {symbol} {quantity} @ ${fill_price:.2f}")

        return order

    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Order:
        """Simulate limit order (simplified - marks as pending)"""
        symbol = self.normalize_symbol(symbol)
        order_id = str(uuid.uuid4())

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type='limit',
            quantity=quantity,
            price=price,
            status='pending'
        )

        self.state['orders'][order_id] = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'type': 'limit',
            'status': 'pending'
        }

        self._save_state()

        log.info(f"[MOCK] Limit {side} placed: {symbol} {quantity} @ ${price:.2f}")

        return order

    async def place_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float
    ) -> Order:
        """Simulate stop loss order"""
        symbol = self.normalize_symbol(symbol)
        order_id = str(uuid.uuid4())

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type='stop_loss',
            quantity=quantity,
            price=stop_price,
            status='pending'
        )

        self.state['orders'][order_id] = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'stop_price': stop_price,
            'type': 'stop_loss',
            'status': 'pending'
        }

        self._save_state()

        log.info(f"[MOCK] Stop loss placed: {symbol} {quantity} @ ${stop_price:.2f}")

        return order

    async def place_take_profit(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Order:
        """Simulate take profit order"""
        symbol = self.normalize_symbol(symbol)
        order_id = str(uuid.uuid4())

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type='take_profit',
            quantity=quantity,
            price=price,
            status='pending'
        )

        self.state['orders'][order_id] = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'target_price': price,
            'type': 'take_profit',
            'status': 'pending'
        }

        self._save_state()

        log.info(f"[MOCK] Take profit placed: {symbol} {quantity} @ ${price:.2f}")

        return order

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id in self.state['orders']:
            self.state['orders'][order_id]['status'] = 'cancelled'
            self._save_state()
            log.info(f"[MOCK] Order cancelled: {order_id}")
            return True
        return False

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol"""
        symbol = self.normalize_symbol(symbol)
        log.info(f"[MOCK] Leverage set to {leverage}x for {symbol}")
        return True

    async def _update_position(self, symbol: str, side: str, quantity: float, price: float):
        """Update position state after a trade"""
        if symbol in self.state['positions']:
            # Update existing position
            pos = self.state['positions'][symbol]

            if pos['side'] == side:
                # Adding to position
                total_qty = pos['quantity'] + quantity
                avg_price = (pos['entry_price'] * pos['quantity'] + price * quantity) / total_qty
                pos['quantity'] = total_qty
                pos['entry_price'] = avg_price
            else:
                # Closing or reversing position
                if quantity >= pos['quantity']:
                    # Close or reverse
                    remaining = quantity - pos['quantity']
                    if remaining > 0:
                        # Reverse position
                        pos['side'] = side
                        pos['quantity'] = remaining
                        pos['entry_price'] = price
                    else:
                        # Close position
                        del self.state['positions'][symbol]
                else:
                    # Partial close
                    pos['quantity'] -= quantity
        else:
            # New position
            self.state['positions'][symbol] = {
                'side': 'long' if side == 'buy' else 'short',
                'quantity': quantity,
                'entry_price': price,
                'leverage': settings.default_leverage,
                'opened_at': datetime.now().isoformat()
            }

        # Update balance
        self._update_balance()

    def _update_balance(self):
        """Recalculate available balance based on positions"""
        total_in_positions = 0.0

        for symbol, pos in self.state['positions'].items():
            # Margin used = position value / leverage
            position_value = pos['quantity'] * pos['entry_price']
            margin_used = position_value / pos['leverage']
            total_in_positions += margin_used

        self.state['balance']['in_positions'] = total_in_positions
        self.state['balance']['available'] = self.state['balance']['total'] - total_in_positions
