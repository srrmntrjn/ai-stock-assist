"""Exchange abstraction layer providing a unified exchange interface."""

from src.config import settings
from src.exchanges.base import BaseExchange
from src.exchanges.deribit_exchange import DeribitExchange
from src.exchanges.mock_exchange import MockExchange


def get_exchange() -> BaseExchange:
    """Factory function that returns the configured exchange implementation."""

    exchange_name = settings.exchange.lower()

    if exchange_name == "mock":
        return MockExchange()

    if exchange_name == "deribit":
        return DeribitExchange(
            api_key=settings.exchange_api_key,
            secret=settings.exchange_secret,
            testnet=settings.environment == "testnet",
        )

    if exchange_name == "coinbase":
        raise NotImplementedError(
            "Coinbase exchange support is not implemented yet."
        )

    raise ValueError(f"Unsupported exchange configured: {settings.exchange}")


__all__ = ["BaseExchange", "MockExchange", "DeribitExchange", "get_exchange"]
