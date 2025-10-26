"""Exchange abstraction layer and factory helpers."""

from src.config import settings
from src.logger import log
from src.exchanges.base import BaseExchange
from src.exchanges.deribit_exchange import DeribitExchange
from src.exchanges.mock_exchange import MockExchange


def get_exchange() -> BaseExchange:
    """Create an exchange instance based on configuration."""

    exchange_name = settings.exchange.lower()

    if exchange_name == "mock":
        log.info("Using mock exchange (paper trading mode)")
        return MockExchange()

    if exchange_name == "deribit":
        return DeribitExchange(
            api_key=settings.exchange_api_key,
            secret=settings.exchange_secret,
            testnet=settings.environment == "testnet",
        )

    if exchange_name == "coinbase":
        raise NotImplementedError("Coinbase exchange integration is not yet implemented")

    raise ValueError(f"Unsupported exchange configured: {settings.exchange}")


__all__ = ["BaseExchange", "DeribitExchange", "MockExchange", "get_exchange"]
