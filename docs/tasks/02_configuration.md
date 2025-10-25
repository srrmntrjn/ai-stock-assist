# Task 02: Configuration Module

**Status:** ✅ COMPLETED

**Estimated Time:** 30 minutes

---

## Overview

Create a centralized configuration system using Pydantic Settings that loads from environment variables and validates configuration.

---

## Implementation Details

### File: `src/config.py`

**Key Features:**
1. **Type-safe settings** using Pydantic
2. **Automatic .env loading**
3. **Validation** of required fields
4. **Helper properties** for easy access

### Configuration Structure

```python
class Settings(BaseSettings):
    # Exchange Configuration
    exchange: Literal["mock", "coinbase"]
    environment: Literal["testnet", "production"]

    # API Keys
    anthropic_api_key: str
    openai_api_key: str
    coinbase_api_key: str
    coinbase_secret: str

    # Trading Configuration
    initial_balance: float
    symbols: str  # Comma-separated
    default_leverage: int
    max_position_size_pct: float
    max_simultaneous_positions: int

    # Bot Settings
    run_interval_minutes: int
    enable_trading: bool

    # Risk Management
    max_drawdown_pct: float
    position_size_pct: float

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    log_file: str
```

### Helper Properties

```python
@property
def symbol_list(self) -> List[str]:
    """Parse symbols from comma-separated string"""
    return [s.strip() for s in self.symbols.split(",")]

@property
def exchange_api_key(self) -> str:
    """Get appropriate API key based on exchange"""
    # Returns correct key for mock/coinbase

@property
def exchange_secret(self) -> str:
    """Get appropriate secret based on exchange"""
```

### Validation

```python
def validate_config(self) -> None:
    """Validate that required configuration is present"""
    # Checks:
    # - Exchange credentials are present
    # - AI model credentials are present
    # - Raises ValueError with helpful messages if missing
```

---

## Usage

```python
from src.config import settings

# Access settings
print(settings.initial_balance)  # 10000.0
print(settings.symbol_list)      # ['BTC-PERPETUAL', 'ETH-PERPETUAL', ...]
print(settings.exchange)          # 'mock'

# Validate before running
settings.validate_config()
```

---

## Environment Variables

All settings are loaded from `.env` file or environment variables:

```bash
# Required for Mock Exchange
EXCHANGE=mock
ANTHROPIC_API_KEY=sk-ant-...

# Required for Coinbase Production
EXCHANGE=coinbase
COINBASE_API_KEY=...
COINBASE_SECRET=...
```

---

## Benefits

1. **Type Safety:** Pydantic validates types automatically
2. **IDE Support:** Autocomplete and type hints
3. **Easy Testing:** Can override settings programmatically
4. **Validation:** Catches config errors early
5. **Defaults:** Sensible defaults for all settings

---

## Testing

```python
# Test configuration loading
from src.config import settings

assert settings.exchange in ['mock', 'coinbase']
assert settings.initial_balance > 0
assert len(settings.symbol_list) == 6

print("✓ Configuration loaded successfully")
```

---

## Common Issues

**Issue:** `ValueError: Missing Anthropic API key`
**Solution:** Add `ANTHROPIC_API_KEY=sk-ant-...` to `.env`

**Issue:** `ValidationError` on startup
**Solution:** Check `.env` file for typos or missing values

---

## Next Steps

→ [Task 03: Logging System](03_logging.md)
