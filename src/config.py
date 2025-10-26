"""Configuration management using Pydantic settings"""

from typing import List, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Exchange Configuration
    exchange: Literal["mock", "deribit", "coinbase"] = Field(default="mock")
    environment: Literal["testnet", "production"] = Field(default="testnet")

    # Deribit API Keys
    deribit_testnet_api_key: str = Field(default="")
    deribit_testnet_secret: str = Field(default="")
    deribit_api_key: str = Field(default="")
    deribit_secret: str = Field(default="")

    # Coinbase API Keys
    coinbase_api_key: str = Field(default="")
    coinbase_secret: str = Field(default="")

    # AI Model Configuration
    ai_model: Literal["mock", "claude", "openai"] = Field(default="mock")
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")

    # Trading Configuration
    initial_balance: float = Field(default=10000.0)
    symbols: str = Field(
        default="BTC-PERPETUAL,ETH-PERPETUAL,SOL-PERPETUAL,BNB-PERPETUAL,XRP-PERPETUAL,DOGE-PERPETUAL"
    )
    default_leverage: int = Field(default=20, ge=1, le=100)
    max_position_size_pct: float = Field(default=25.0, ge=1, le=100)
    max_simultaneous_positions: int = Field(default=3, ge=1)

    # Bot Settings
    run_interval_minutes: int = Field(default=3, ge=1)
    enable_trading: bool = Field(default=True)

    # Risk Management
    max_drawdown_pct: float = Field(default=20.0, ge=1, le=100)
    position_size_pct: float = Field(default=20.0, ge=1, le=100)

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_file: str = Field(default="logs/trading_bot.log")

    @property
    def symbol_list(self) -> List[str]:
        """Parse symbols from comma-separated string"""
        return [s.strip() for s in self.symbols.split(",")]

    @property
    def exchange_api_key(self) -> str:
        """Get the appropriate API key based on exchange and environment"""
        if self.exchange == "deribit":
            if self.environment == "testnet":
                return self.deribit_testnet_api_key
            return self.deribit_api_key
        elif self.exchange == "coinbase":
            return self.coinbase_api_key
        return ""

    @property
    def exchange_secret(self) -> str:
        """Get the appropriate secret based on exchange and environment"""
        if self.exchange == "deribit":
            if self.environment == "testnet":
                return self.deribit_testnet_secret
            return self.deribit_secret
        elif self.exchange == "coinbase":
            return self.coinbase_secret
        return ""

    def validate_config(self) -> None:
        """Validate that required configuration is present"""
        errors = []

        # Check exchange credentials (skip for mock exchange)
        if self.exchange != "mock":
            if not self.exchange_api_key:
                errors.append(f"Missing API key for {self.exchange} ({self.environment})")
            if not self.exchange_secret:
                errors.append(f"Missing secret for {self.exchange} ({self.environment})")

        # Check AI credentials
        if self.ai_model == "claude" and not self.anthropic_api_key:
            errors.append("Missing Anthropic API key")
        elif self.ai_model == "openai" and not self.openai_api_key:
            errors.append("Missing OpenAI API key")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))


# Global settings instance
settings = Settings()
