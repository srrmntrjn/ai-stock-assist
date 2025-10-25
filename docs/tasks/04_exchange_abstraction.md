# Task 04: Exchange Abstraction Layer

**Status:** ✅ COMPLETED

**Estimated Time:** 1 hour

---

## Overview

Design an abstract base class for exchanges that allows seamless switching between MockExchange (testing) and CoinbaseExchange (production) without changing bot code.

---

## Implementation Details

### File: `src/exchanges/base.py`

**Purpose:** Define interface that all exchanges must implement

### Core Data Classes

```python
@dataclass
class OHLCV:
    """OHLCV candle data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class Position:
    """Open position information"""
    symbol: str
    side: str  # "long" or "short"
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    liquidation_price: Optional[float]
    leverage: Optional[int]

@dataclass
class Order:
    """Order information"""
    order_id: str
    symbol: str
    side: str  # "buy" or "sell"
    order_type: str  # "market", "limit", "stop_loss", "take_profit"
    quantity: float
    price: Optional[float]
    status: str  # "pending", "filled", "cancelled"

@dataclass
class Balance:
    """Account balance"""
    total: float
    available: float
    in_positions: float
```

### Abstract Exchange Interface

```python
class BaseExchange(ABC):
    """Abstract base class for all exchanges"""

    @abstractmethod
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[OHLCV]:
        """Fetch OHLCV candle data"""

    @abstractmethod
    async def get_open_interest(self, symbol: str) -> float:
        """Get current open interest"""

    @abstractmethod
    async def get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate"""

    @abstractmethod
    async def get_balance(self) -> Balance:
        """Get account balance"""

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""

    @abstractmethod
    async def place_market_order(self, symbol: str, side: str, quantity: float) -> Order:
        """Place a market order"""

    @abstractmethod
    async def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Order:
        """Place a limit order"""

    @abstractmethod
    async def place_stop_loss(self, symbol: str, side: str, quantity: float, stop_price: float) -> Order:
        """Place a stop loss order"""

    @abstractmethod
    async def place_take_profit(self, symbol: str, side: str, quantity: float, price: float) -> Order:
        """Place a take profit order"""

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""

    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol"""

    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for this exchange"""
```

---

## Usage Pattern

```python
# In your bot code
from src.config import settings
from src.exchanges import MockExchange, CoinbaseExchange

# Factory pattern
def get_exchange() -> BaseExchange:
    if settings.exchange == "mock":
        return MockExchange()
    elif settings.exchange == "coinbase":
        return CoinbaseExchange(
            api_key=settings.exchange_api_key,
            secret=settings.exchange_secret
        )

# Use the exchange
exchange = get_exchange()

# Fetch data (works with any exchange!)
candles = await exchange.get_ohlcv("BTC-PERPETUAL", "3m", 100)
balance = await exchange.get_balance()
positions = await exchange.get_positions()

# Place orders (works with any exchange!)
order = await exchange.place_market_order("BTC-PERPETUAL", "buy", 0.1)
```

---

## Benefits

### 1. **Seamless Testing → Production**
```python
# Testing
EXCHANGE=mock

# Production (just change .env!)
EXCHANGE=coinbase
```

### 2. **Same Code, Different Backends**
Your bot doesn't need to know if it's talking to:
- MockExchange (simulated)
- CoinbaseExchange (real money)
- Future exchanges (Binance, Kraken, etc.)

### 3. **Type Safety**
All data classes are strongly typed:
```python
balance: Balance = await exchange.get_balance()
print(balance.available)  # IDE autocomplete works!
```

### 4. **Easy to Add New Exchanges**
Just implement `BaseExchange` interface:
```python
class KrakenExchange(BaseExchange):
    async def get_ohlcv(self, ...):
        # Kraken-specific implementation
```

---

## Design Decisions

### Why Async?
- Prepares for future websocket integration
- Non-blocking API calls
- Better performance with multiple requests

### Why Dataclasses?
- Immutable data structures
- Type hints
- Easy serialization to JSON

### Why Abstract Base Class?
- Enforces interface compliance
- Catches missing methods at import time
- Clear contract for implementations

---

## Testing

```python
from src.exchanges.mock_exchange import MockExchange

# Test the interface
async def test_exchange():
    exchange = MockExchange()

    # Test data fetching
    candles = await exchange.get_ohlcv("BTC-PERPETUAL", "3m", 10)
    assert len(candles) == 10
    assert isinstance(candles[0], OHLCV)

    # Test balance
    balance = await exchange.get_balance()
    assert balance.total > 0

    # Test order placement
    order = await exchange.place_market_order("BTC-PERPETUAL", "buy", 0.1)
    assert order.status == "filled"

    print("✓ Exchange interface works!")
```

---

## Next Steps

→ [Task 05: Market Data Fetcher](05_data_fetcher.md)
→ [Task 07: Mock Exchange Implementation](07_mock_exchange.md)
→ [Task 08: Coinbase Exchange Implementation](08_coinbase_exchange.md)
