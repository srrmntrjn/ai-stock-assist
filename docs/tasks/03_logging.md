# Task 03: Logging System

**Status:** ✅ COMPLETED

**Estimated Time:** 20 minutes

---

## Overview

Set up a comprehensive logging system using Loguru for both console and file output with rotation and compression.

---

## Implementation Details

### File: `src/logger.py`

**Features:**
1. **Console output** with color-coding
2. **File output** with rotation (100 MB)
3. **Compression** (old logs saved as .zip)
4. **Retention** (30 days)
5. **Configurable log level** from settings

### Logger Configuration

```python
def setup_logger():
    """Configure loguru logger"""

    # Console output with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )

    # File output with rotation
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="100 MB",
        retention="30 days",
        compression="zip",
    )
```

---

## Usage

```python
from src.logger import log

# Different log levels
log.debug("Detailed debugging info")
log.info("General information")
log.warning("Warning message")
log.error("Error occurred")

# With variables
log.info(f"Price fetched: ${price:.2f}")

# In exceptions
try:
    # code
except Exception as e:
    log.error(f"Failed to execute: {e}")
    raise
```

---

## Log Levels

Set in `.env`:

```bash
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

**DEBUG:** Very detailed logs (all operations)
**INFO:** Normal operations (default)
**WARNING:** Warning messages only
**ERROR:** Errors only

---

## Log Format

### Console Output (Colored):
```
2025-10-25 10:30:45 | INFO     | src.main:run - Bot started
2025-10-25 10:30:46 | DEBUG    | src.exchanges.mock_exchange:get_price - Fetched price for BTC: $111340.50
2025-10-25 10:30:47 | INFO     | src.trading.engine:place_order - [MOCK] Market buy filled: BTC 0.1 @ $111340.50
```

### File Output (Plain):
```
2025-10-25 10:30:45 | INFO     | src.main:run:45 - Bot started
2025-10-25 10:30:46 | DEBUG    | src.exchanges.mock_exchange:get_price:112 - Fetched price for BTC: $111340.50
```

---

## Log Rotation

Logs automatically rotate when they reach 100 MB:
```
logs/
├── trading_bot.log          # Current log
├── trading_bot.2025-10-24.log.zip
└── trading_bot.2025-10-23.log.zip
```

Old logs are automatically deleted after 30 days.

---

## Benefits

1. **Debugging:** Easy to trace bot decisions
2. **Monitoring:** Track performance over time
3. **Audit Trail:** All trades logged
4. **Error Tracking:** Catch and diagnose issues
5. **Production Ready:** Automatic rotation prevents disk fill

---

## Log Examples

```python
# Market data fetch
log.debug(f"Fetched {len(candles)} candles for {symbol}")

# AI decision
log.info(f"AI Decision: {decision['action']} {symbol} (confidence: {decision['confidence']:.2f})")

# Trade execution
log.info(f"[MOCK] Market buy filled: {symbol} {quantity} @ ${price:.2f}")

# Error handling
log.error(f"Failed to fetch OHLCV for {symbol}: {e}")

# Portfolio update
log.info(f"Portfolio value: ${value:.2f} | Return: {return_pct:.2f}%")
```

---

## Testing

```python
from src.logger import log

log.info("Logger test - INFO level")
log.debug("Logger test - DEBUG level")
log.warning("Logger test - WARNING level")
log.error("Logger test - ERROR level")

# Check logs directory
ls logs/
# Should see: trading_bot.log
```

---

## Next Steps

→ [Task 04: Exchange Abstraction](04_exchange_abstraction.md)
