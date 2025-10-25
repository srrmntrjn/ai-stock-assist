# Task 09: AI System Prompt Builder

**Status:** ⏭️ NEXT

**Estimated Time:** 1 hour

---

## Overview

Build a system prompt formatter that takes market data, technical indicators, and portfolio state, and formats it into a structured prompt for the AI model to analyze.

---

## Implementation Details

### File: `src/ai/prompt_builder.py`

**Purpose:** Format market data into the AI prompt shown in your example

### Prompt Structure

Based on your example prompt, the builder should generate:

```
It has been {invocation_count} invocations since you started trading.
The current time is {current_time}.

Below, we are providing you with a variety of state data, price data, and predictive signals.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

CURRENT MARKET STATE FOR ALL COINS

ALL BTC DATA
current_price = {price}, current_ema20 = {ema20}, current_macd = {macd}, current_rsi (7 period) = {rsi7}

Open Interest: Latest: {oi_latest} Average: {oi_avg}
Funding Rate: {funding_rate}

Intraday series (3-minute intervals, oldest → latest):
Mid prices: [{price_series}]
EMA indicators (20-period): [{ema_series}]
MACD indicators: [{macd_series}]
RSI indicators (7-Period): [{rsi7_series}]
RSI indicators (14-Period): [{rsi14_series}]

Longer-term context (4-hour timeframe):
20-Period EMA: {ema20_4h} vs. 50-Period EMA: {ema50_4h}
3-Period ATR: {atr3_4h} vs. 14-Period ATR: {atr14_4h}
Current Volume: {volume_4h} vs. Average Volume: {avg_volume_4h}
MACD indicators: [{macd_4h_series}]
RSI indicators (14-Period): [{rsi14_4h_series}]

[... repeat for ETH, SOL, BNB, XRP, DOGE ...]

HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): {return_pct}%
Available Cash: {cash}
Current Account Value: {account_value}
Current live positions & performance: {positions_json}
Sharpe Ratio: {sharpe}
```

---

## Class Structure

```python
class PromptBuilder:
    """Builds AI system prompts from market data"""

    def __init__(self, invocation_count: int = 0):
        self.invocation_count = invocation_count

    def build_prompt(
        self,
        market_data: Dict[str, Any],  # All indicators per symbol
        portfolio_state: Dict[str, Any],  # Account info
        positions: List[Position]
    ) -> str:
        """Build complete system prompt"""

        prompt_parts = []

        # Header
        prompt_parts.append(self._build_header())

        # Market data for each coin
        for symbol in settings.symbol_list:
            coin_data = market_data.get(symbol, {})
            prompt_parts.append(self._build_coin_section(symbol, coin_data))

        # Portfolio section
        prompt_parts.append(self._build_portfolio_section(portfolio_state, positions))

        return "\n\n".join(prompt_parts)

    def _build_header(self) -> str:
        """Build prompt header"""
        return f"""It has been {self.invocation_count} invocations since you started trading.
The current time is {datetime.now()}.

Below, we are providing you with a variety of state data, price data, and predictive signals.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

CURRENT MARKET STATE FOR ALL COINS"""

    def _build_coin_section(self, symbol: str, data: Dict) -> str:
        """Build section for one coin"""
        coin = symbol.replace('-PERPETUAL', '')

        intraday = data.get('intraday', {})
        longer_term = data.get('longer_term', {})

        return f"""ALL {coin} DATA
current_price = {intraday.get('current_price')}, current_ema20 = {intraday.get('current_ema20')}, current_macd = {intraday.get('current_macd')}, current_rsi (7 period) = {intraday.get('current_rsi_7')}

Open Interest: Latest: {data.get('open_interest')} Average: {data.get('open_interest_avg')}
Funding Rate: {data.get('funding_rate')}

Intraday series (3-minute intervals, oldest → latest):
Mid prices: {intraday.get('prices')}
EMA indicators (20-period): {intraday.get('ema_20')}
MACD indicators: {intraday.get('macd')}
RSI indicators (7-Period): {intraday.get('rsi_7')}
RSI indicators (14-Period): {intraday.get('rsi_14')}

Longer-term context (4-hour timeframe):
20-Period EMA: {longer_term.get('ema_20')} vs. 50-Period EMA: {longer_term.get('ema_50')}
3-Period ATR: {longer_term.get('atr_3')} vs. 14-Period ATR: {longer_term.get('atr_14')}
Current Volume: {longer_term.get('current_volume')} vs. Average Volume: {longer_term.get('avg_volume')}
MACD indicators: {longer_term.get('macd')}
RSI indicators (14-Period): {longer_term.get('rsi_14')}"""

    def _build_portfolio_section(self, portfolio: Dict, positions: List[Position]) -> str:
        """Build portfolio & account section"""
        positions_formatted = []
        for pos in positions:
            positions_formatted.append({
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'liquidation_price': pos.liquidation_price,
                'unrealized_pnl': pos.unrealized_pnl,
                'leverage': pos.leverage
            })

        return f"""HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): {portfolio.get('total_return_pct')}%
Available Cash: {portfolio.get('available_cash')}
Current Account Value: {portfolio.get('account_value')}
Current live positions & performance: {json.dumps(positions_formatted, indent=2)}
Sharpe Ratio: {portfolio.get('sharpe_ratio')}"""
```

---

## Data Flow

```
Market Data (from exchange + indicators)
    ↓
PromptBuilder.build_prompt()
    ↓
Formatted System Prompt (string)
    ↓
AI Model
```

---

## Usage Example

```python
from src.ai.prompt_builder import PromptBuilder

# Initialize
prompt_builder = PromptBuilder(invocation_count=2384)

# Gather data
market_data = {
    'BTC-PERPETUAL': {
        'intraday': {...},  # From TechnicalIndicators
        'longer_term': {...},
        'open_interest': 27968.62,
        'funding_rate': 0.0000125
    },
    # ... ETH, SOL, etc.
}

portfolio_state = {
    'total_return_pct': 69.56,
    'available_cash': 97.8,
    'account_value': 16956.08,
    'sharpe_ratio': 0.285
}

positions = await exchange.get_positions()

# Build prompt
system_prompt = prompt_builder.build_prompt(market_data, portfolio_state, positions)

# Send to AI
response = await ai_model.get_decision(system_prompt)
```

---

## Testing

```python
def test_prompt_builder():
    builder = PromptBuilder(invocation_count=100)

    # Mock data
    market_data = {...}
    portfolio = {...}
    positions = []

    prompt = builder.build_prompt(market_data, portfolio, positions)

    # Assertions
    assert "invocation" in prompt.lower()
    assert "BTC" in prompt
    assert "current_price" in prompt
    assert "account_value" in prompt

    print(prompt)  # Visual inspection
    print("✓ Prompt builder works!")
```

---

## Next Steps

→ [Task 10: AI Models Interface](10_ai_models.md)
