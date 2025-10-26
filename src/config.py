"""Configuration management using Pydantic settings."""

from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Exchange Configuration
    exchange: Literal["mock", "coinbase"] = Field(default="mock")
    environment: Literal["testnet", "production"] = Field(default="testnet")

    # API Keys
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    coinbase_api_key: str = Field(default="")
    coinbase_secret: str = Field(default="")

    # Trading Configuration
    initial_balance: float = Field(default=10_000.0)
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
        """Parse symbols from comma-separated string."""

        return [s.strip() for s in self.symbols.split(",") if s.strip()]

    @property
    def exchange_api_key(self) -> str:
        """Return the API key appropriate for the configured exchange."""

        if self.exchange == "coinbase":
            return self.coinbase_api_key.strip()
        # Mock exchange uses internal credentials and therefore does not require a key.
        return ""

    @property
    def exchange_secret(self) -> str:
        """Return the secret appropriate for the configured exchange."""

        if self.exchange == "coinbase":
            return self.coinbase_secret.strip()
        # Mock exchange uses internal credentials and therefore does not require a secret.
        return ""

    def validate_config(self) -> None:
        """Validate that required configuration is present."""

        errors = []

        if self.exchange == "coinbase":
            if not self.coinbase_api_key.strip():
                errors.append("Missing Coinbase API key")
            if not self.coinbase_secret.strip():
                errors.append("Missing Coinbase secret")

        if not self.anthropic_api_key.strip():
            errors.append("Missing Anthropic API key")
        if not self.openai_api_key.strip():
            errors.append("Missing OpenAI API key")

        if errors:
            message = "Configuration errors:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(message)


# Global settings instance
settings = Settings()
