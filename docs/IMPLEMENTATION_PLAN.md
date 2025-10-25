# AI Trading Bot - Implementation Plan

## Project Overview

**Goal:** Build an AI-powered crypto trading bot that:
- Runs every 3 minutes
- Analyzes market data using technical indicators
- Uses LLM (Claude/GPT) to make BUY/SELL/HOLD decisions
- Trades 6 crypto perpetual futures: BTC, ETH, SOL, BNB, XRP, DOGE
- Starts with paper trading (mock exchange)
- Transitions to production (Coinbase Financial Markets)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              SCHEDULER (Every 3 minutes)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                MAIN ORCHESTRATOR                        │
│  1. Fetch market data (OHLCV, OI, Funding)            │
│  2. Calculate technical indicators                      │
│  3. Build AI system prompt                             │
│  4. Get AI trading decision                            │
│  5. Execute trades via exchange                        │
│  6. Update positions & portfolio                       │
│  7. Log everything                                     │
└─────────────────────────────────────────────────────────┘
         │           │              │            │
         ▼           ▼              ▼            ▼
    ┌────────┐  ┌────────┐   ┌──────────┐  ┌─────────┐
    │ Data   │  │   AI   │   │ Trading  │  │Portfolio│
    │Fetcher │  │ Models │   │  Engine  │  │ Manager │
    └────────┘  └────────┘   └──────────┘  └─────────┘
         │                          │
         ▼                          ▼
    ┌─────────────────────────────────────┐
    │      Exchange Layer (Abstraction)   │
    │  - MockExchange (testing)           │
    │  - CoinbaseExchange (production)    │
    └─────────────────────────────────────┘
```

---

## Project Structure

```
ai-stock-assist/
├── README.md
├── requirements.txt
├── .env                          # API keys (gitignored)
├── .env.example
├── docs/
│   ├── IMPLEMENTATION_PLAN.md    # This file
│   └── tasks/                    # Individual task docs
│       ├── 01_project_setup.md
│       ├── 02_configuration.md
│       ├── 03_logging.md
│       ├── ...
├── src/
│   ├── __init__.py
│   ├── config.py                 # Settings management
│   ├── logger.py                 # Logging configuration
│   ├── main.py                   # Main entry point
│   ├── scheduler.py              # APScheduler setup
│   ├── data/
│   │   ├── __init__.py
│   │   └── indicators.py         # Technical indicators
│   ├── exchanges/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract exchange interface
│   │   ├── data_fetcher.py      # Free market data APIs
│   │   ├── mock_exchange.py     # Paper trading simulator
│   │   └── coinbase_exchange.py # Production exchange
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base_model.py        # Abstract AI interface
│   │   ├── claude_model.py      # Claude implementation
│   │   ├── openai_model.py      # OpenAI implementation
│   │   ├── prompt_builder.py    # Build system prompts
│   │   └── response_parser.py   # Parse AI decisions
│   ├── trading/
│   │   ├── __init__.py
│   │   ├── engine.py            # Order execution
│   │   ├── position_manager.py  # Position tracking
│   │   └── risk_manager.py      # Risk controls
│   └── portfolio/
│       ├── __init__.py
│       └── tracker.py           # Portfolio metrics
├── logs/                        # Logs (gitignored)
├── data/                        # State files (gitignored)
│   ├── portfolio_state.json
│   ├── trade_history.json
│   └── mock_exchange_state.json
└── tests/
    └── ...
```

---

## Implementation Phases

### ✅ **Phase 1: Foundation** (COMPLETED)
- [x] Project structure and dependencies
- [x] Configuration management (Pydantic settings)
- [x] Logging system (Loguru)
- [x] Exchange abstraction layer
- [x] Free market data fetcher (CoinGecko)
- [x] Technical indicators calculator (pandas-ta)
- [x] Mock exchange simulator

**Status:** Infrastructure complete, ready for AI integration

---

### 🔄 **Phase 2: AI Integration** (NEXT)
- [ ] System prompt builder
- [ ] AI model interface (Claude + OpenAI)
- [ ] AI response parser
- [ ] Trading decision logic

**Estimated Time:** 2-3 hours

**Details:** See `docs/tasks/09_prompt_builder.md`, `10_ai_models.md`, `11_ai_parser.md`

---

### **Phase 3: Trading Engine**
- [ ] Order execution engine
- [ ] Position manager
- [ ] Risk management system
- [ ] Portfolio tracker

**Estimated Time:** 2-3 hours

**Details:** See `docs/tasks/12_position_manager.md`, `13_risk_management.md`, `14_portfolio_tracker.md`

---

### **Phase 4: Orchestration**
- [ ] Main orchestrator (ties everything together)
- [ ] Scheduler (runs every 3 minutes)
- [ ] Error handling & recovery

**Estimated Time:** 1-2 hours

**Details:** See `docs/tasks/16_orchestrator.md`, `15_scheduler.md`

---

### **Phase 5: Testing & Deployment**
- [ ] End-to-end testing with mock exchange
- [ ] Performance monitoring
- [ ] Deployment scripts (Docker, Railway.app)
- [ ] Production cutover to Coinbase

**Estimated Time:** 2-3 hours

**Details:** See `docs/tasks/17_testing.md`, `18_deployment.md`

---

## Technology Stack

### **Languages & Frameworks**
- Python 3.10+
- asyncio for async operations

### **Data & Exchange APIs**
- `ccxt` - Unified exchange API library
- `requests` - HTTP client
- `pandas` / `pandas-ta` - Data processing & technical analysis

### **AI Models**
- `anthropic` - Claude API
- `openai` - OpenAI API

### **Utilities**
- `pydantic` / `pydantic-settings` - Configuration & validation
- `loguru` - Logging
- `APScheduler` - Job scheduling
- `python-dotenv` - Environment variables

---

## Configuration

### **Environment Variables** (.env)

```bash
# Exchange
EXCHANGE=mock                    # Options: mock, coinbase
ENVIRONMENT=testnet              # Options: testnet, production

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
COINBASE_API_KEY=...             # For production
COINBASE_SECRET=...

# Trading
INITIAL_BALANCE=10000.00
SYMBOLS=BTC-PERPETUAL,ETH-PERPETUAL,SOL-PERPETUAL,BNB-PERPETUAL,XRP-PERPETUAL,DOGE-PERPETUAL
DEFAULT_LEVERAGE=20
MAX_POSITION_SIZE_PCT=25
MAX_SIMULTANEOUS_POSITIONS=3

# Bot Settings
RUN_INTERVAL_MINUTES=3
ENABLE_TRADING=true

# Risk Management
MAX_DRAWDOWN_PCT=20
POSITION_SIZE_PCT=20

# AI
AI_MODEL=claude                  # Options: claude, openai
```

---

## Key Features

### **1. Exchange Abstraction**
- Same code works with MockExchange (testing) and CoinbaseExchange (production)
- Seamless cutover: just change `.env` config
- All exchanges implement `BaseExchange` interface

### **2. Real Market Data (Free)**
- Fetches live prices from CoinGecko API
- Calculates technical indicators locally
- No API costs for market data

### **3. AI-Powered Decisions**
- Pluggable AI models (Claude, GPT, others)
- Structured prompts with market data
- Parsed JSON responses

### **4. Risk Management**
- Position sizing based on account %
- Max leverage limits
- Max simultaneous positions
- Drawdown protection

### **5. Portfolio Tracking**
- Real-time PnL calculation
- Sharpe ratio
- Win rate, total return
- Trade history

---

## Testing Strategy

### **Phase 1: Mock Exchange (Current)**
- Run bot with `EXCHANGE=mock`
- Uses REAL market data
- Simulates order execution
- Tracks paper trading results
- Zero financial risk

### **Phase 2: Production (Later)**
- Open Coinbase Financial Markets account
- Start with small capital ($500-1000)
- Switch `EXCHANGE=coinbase`
- Same code, real money

---

## Development Workflow

1. **Build feature** in isolated module
2. **Write tests** (optional but recommended)
3. **Test with mock exchange**
4. **Monitor logs** for errors
5. **Iterate & improve**
6. **Deploy to production** when profitable

---

## Deployment Options

### **Option 1: Railway.app** (Recommended)
- One-click deploy from GitHub
- $5/month for 24/7 uptime
- Auto-deploys on git push

### **Option 2: DigitalOcean**
- $5/month droplet
- More control, manual setup

### **Option 3: AWS/GCP**
- Free tier available
- More complex setup

### **Option 4: Local (Testing)**
- Run on your machine
- Use `screen` or `tmux` to keep running

---

## Next Steps

1. ✅ Review this implementation plan
2. ⏭️ Continue building AI integration (Phase 2)
3. ⏭️ Build trading engine (Phase 3)
4. ⏭️ Integrate orchestrator (Phase 4)
5. ⏭️ Test end-to-end (Phase 5)
6. ⏭️ Deploy & monitor

---

## Task Breakdown

See individual task documents in `docs/tasks/` for detailed implementation guides:

1. [Project Setup](tasks/01_project_setup.md) ✅
2. [Configuration Module](tasks/02_configuration.md) ✅
3. [Logging System](tasks/03_logging.md) ✅
4. [Exchange Abstraction](tasks/04_exchange_abstraction.md) ✅
5. [Market Data Fetcher](tasks/05_data_fetcher.md) ✅
6. [Technical Indicators](tasks/06_technical_indicators.md) ✅
7. [Mock Exchange](tasks/07_mock_exchange.md) ✅
8. [Coinbase Exchange](tasks/08_coinbase_exchange.md) ⏳
9. [Prompt Builder](tasks/09_prompt_builder.md) ⏭️
10. [AI Models](tasks/10_ai_models.md) ⏭️
11. [AI Response Parser](tasks/11_ai_parser.md) ⏭️
12. [Position Manager](tasks/12_position_manager.md) ⏭️
13. [Risk Management](tasks/13_risk_management.md) ⏭️
14. [Portfolio Tracker](tasks/14_portfolio_tracker.md) ⏭️
15. [Scheduler](tasks/15_scheduler.md) ⏭️
16. [Main Orchestrator](tasks/16_orchestrator.md) ⏭️
17. [Testing](tasks/17_testing.md) ⏭️
18. [Deployment](tasks/18_deployment.md) ⏭️

---

**Total Estimated Time:** 10-15 hours
**Current Progress:** ~40% complete (infrastructure done)
**Next Priority:** AI Integration (Phase 2)
