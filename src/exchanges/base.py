"""Base exchange interface for abstraction"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


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
class OrderBook:
    """Order book snapshot"""
    timestamp: datetime
    bids: List[tuple]  # [(price, size), ...]
    asks: List[tuple]


@dataclass
class Position:
    """Open position information"""
    symbol: str
    side: str  # "long" or "short"
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    liquidation_price: Optional[float] = None
    leverage: Optional[int] = None


@dataclass
class Order:
    """Order information"""
    order_id: str
    symbol: str
    side: str  # "buy" or "sell"
    order_type: str  # "market", "limit", "stop_loss", "take_profit"
    quantity: float
    price: Optional[float] = None
    status: str = "pending"  # "pending", "filled", "cancelled"


@dataclass
class Balance:
    """Account balance"""
    total: float
    available: float
    in_positions: float


class BaseExchange(ABC):
    """Abstract base class for exchange implementations"""

    def __init__(self, api_key: str, secret: str, testnet: bool = True):
        self.api_key = api_key
        self.secret = secret
        self.testnet = testnet

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "3m",
        limit: int = 100
    ) -> List[OHLCV]:
        """Fetch OHLCV candle data"""
        pass

    @abstractmethod
    async def get_open_interest(self, symbol: str) -> float:
        """Get current open interest for a perpetual future"""
        pass

    @abstractmethod
    async def get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate for a perpetual future"""
        pass

    @abstractmethod
    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        """Get order book snapshot"""
        pass

    @abstractmethod
    async def get_balance(self) -> Balance:
        """Get account balance"""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        pass

    @abstractmethod
    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Order:
        """Place a market order"""
        pass

    @abstractmethod
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Order:
        """Place a limit order"""
        pass

    @abstractmethod
    async def place_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float
    ) -> Order:
        """Place a stop loss order"""
        pass

    @abstractmethod
    async def place_take_profit(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Order:
        """Place a take profit order"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass

    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol"""
        pass

    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for this exchange"""
        pass
