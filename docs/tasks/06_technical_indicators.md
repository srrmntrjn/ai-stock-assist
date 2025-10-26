# Task 06: Technical Indicators

**Status:** ✅ COMPLETED

**Estimated Time:** 45 minutes

---

## Overview

Build a reusable module that calculates core technical indicators (EMA, MACD, RSI, ATR) across multiple timeframes using free market data. The output feeds higher-level trading logic and AI prompts.

---

## Implementation Details

### File: `src/indicators/technical.py`

**Key Features:**

1. **`IndicatorConfig`** — Frozen dataclass with indicator lengths, candle limit, and default timeframes (3m & 4h).
2. **`IndicatorSnapshot`** — Dataclass that captures the latest indicator values and provides a `.to_dict()` helper for serialization.
3. **`TechnicalIndicatorCalculator`** — Main service class that:
   - Fetches OHLCV candles via `MarketDataFetcher`.
   - Normalizes timestamps from dicts or `OHLCV` dataclasses.
   - Computes EMA (fast/slow), MACD (line/signal/histogram), RSI, and ATR with `pandas-ta`.
   - Produces human-friendly trend labels (`bullish`, `bearish`, `neutral`).
   - Returns indicator snapshots per timeframe.

### Indicator Pipeline

```python
calculator = TechnicalIndicatorCalculator()
result = calculator.calculate_for_symbol("BTC-PERPETUAL")

three_min = result["3m"].to_dict()
four_hour = result["4h"].to_dict()
```

---

## Error Handling

- Raises a descriptive `ValueError` if no candles are supplied or timestamps cannot be parsed.
- Validates MACD output to guard against unexpected pandas-ta returns.
- Logs debug entries for each calculation step for easy troubleshooting.

---

## Dependencies

- `pandas`
- `pandas-ta`

Ensure these libraries are installed (already listed in `requirements.txt`).

---

## Next Steps

- Feed the snapshot data into the upcoming prompt builder (Task 09).
- Extend configuration to support additional timeframes or custom indicator lengths as needed.
