# AI Trading Bot for Crypto Perpetual Futures

An AI-powered crypto trading bot that uses Claude/GPT to make trading decisions based on technical analysis and market data.

## 🚀 Features

- **AI-Powered Decisions:** Uses Claude (Anthropic) or GPT (OpenAI) for trading decisions
- **6 Crypto Assets:** Trades BTC, ETH, SOL, BNB, XRP, DOGE perpetual futures
- **Technical Analysis:** EMA, MACD, RSI, ATR indicators on multiple timeframes
- **Paper Trading:** Start with mock exchange simulator (real market data, simulated execution)
- **Production Ready:** Seamless cutover to Coinbase Financial Markets
- **Risk Management:** Position sizing, leverage control, max drawdown protection
- **Automated:** Runs every 3 minutes, 24/7
- **Fully Logged:** Complete audit trail of all decisions and trades

---

## 📋 Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repo-url>
cd ai-stock-assist

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required API keys:
- **Anthropic API key** (for Claude) - Get at https://console.anthropic.com/
- **OpenAI API key** (optional, for GPT) - Get at https://platform.openai.com/

### 3. Run

```bash
# Run one iteration (testing)
python src/main.py

# Run continuously (production)
python src/scheduler.py
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              SCHEDULER (Every 3 minutes)                │
└────────────────────┬────────────────────────────────────┘
                     ▼
             MAIN ORCHESTRATOR
         ┌───────────┴───────────┐
         ▼                       ▼
    Market Data              AI Model
    - CoinGecko API         - Claude/GPT
    - Technical Indicators   - Prompt Builder
         ▼                       ▼
    Exchange Layer          Trading Decision
    - MockExchange          - BUY/SELL/HOLD
    - CoinbaseExchange      - Stop Loss/TP
         ▼                       ▼
    Portfolio Tracker       Risk Manager
    - PnL Calculation       - Position Sizing
    - Sharpe Ratio          - Max Exposure
```

---

## 📊 How It Works

1. **Every 3 minutes**, the bot:
   - Fetches live market data (prices, volume, open interest, funding rates)
   - Calculates technical indicators (EMA, MACD, RSI, ATR)
   - Formats data into a system prompt
   - Asks AI: "Should I BUY, SELL, or HOLD?"
   - Executes the AI's decision
   - Updates portfolio and logs performance

2. **AI receives:**
   - Current prices and technical indicators
   - Historical data (last 10 intervals)
   - Longer-term context (4-hour timeframe)
   - Current portfolio state (balance, positions, PnL)

3. **AI returns:**
   - Action: BUY, SELL, or HOLD
   - Symbol: Which crypto to trade
   - Confidence: 0-1 score
   - Stop loss and take profit prices
   - Position size (% of account)
   - Reasoning for the decision

---

## 🎯 Roadmap

### ✅ Phase 1: Infrastructure (COMPLETED)
- [x] Project setup
- [x] Configuration management
- [x] Logging system
- [x] Exchange abstraction layer
- [x] Free market data fetcher
- [x] Technical indicators
- [x] Mock exchange simulator

### 🔄 Phase 2: AI Integration (NEXT)
- [ ] System prompt builder
- [ ] Claude/GPT model interface
- [ ] AI response parser

### ⏭️ Phase 3: Trading Engine
- [ ] Order execution
- [ ] Position manager
- [ ] Risk management
- [ ] Portfolio tracker

### ⏭️ Phase 4: Orchestration
- [ ] Main orchestrator
- [ ] Scheduler (3-minute intervals)
- [ ] Error handling

### ⏭️ Phase 5: Testing & Deployment
- [ ] End-to-end testing
- [ ] Deployment to cloud
- [ ] Production cutover to Coinbase

---

## 📚 Documentation

- **[Implementation Plan](docs/IMPLEMENTATION_PLAN.md)** - Complete project roadmap
- **Task Guides:** See `docs/tasks/` for detailed implementation docs:
  - [01 - Project Setup](docs/tasks/01_project_setup.md)
  - [02 - Configuration](docs/tasks/02_configuration.md)
  - [03 - Logging](docs/tasks/03_logging.md)
  - [04 - Exchange Abstraction](docs/tasks/04_exchange_abstraction.md)
  - [09 - Prompt Builder](docs/tasks/09_prompt_builder.md)
  - [10 - AI Models](docs/tasks/10_ai_models.md)
  - [16 - Main Orchestrator](docs/tasks/16_orchestrator.md)
  - [18 - Deployment Guide](docs/tasks/18_deployment.md)

---

## 🔧 Configuration

Key settings in `.env`:

```bash
# Exchange (mock for testing, coinbase for production)
EXCHANGE=mock

# AI Model (claude or openai)
AI_MODEL=claude
ANTHROPIC_API_KEY=sk-ant-...

# Trading
INITIAL_BALANCE=10000.00
DEFAULT_LEVERAGE=20
MAX_POSITION_SIZE_PCT=25
POSITION_SIZE_PCT=20

# Bot Settings
RUN_INTERVAL_MINUTES=3
ENABLE_TRADING=true

# Risk Management
MAX_DRAWDOWN_PCT=20
```

---

## 🧪 Testing Strategy

### Paper Trading (Current)
- Uses **MockExchange** with real market data
- Simulates order execution locally
- Zero financial risk
- Perfect for strategy testing

### Production (Later)
- Switch `EXCHANGE=coinbase` in `.env`
- Start with small capital ($500-1000)
- Same code, real money

---

## 🚀 Deployment

### Railway.app (Recommended - Easiest)
```bash
# Push to GitHub
git push origin main

# Deploy on Railway
# 1. Create project on railway.app
# 2. Connect GitHub repo
# 3. Add environment variables
# 4. Deploy!

# Cost: $5/month
```

See full deployment guide: [docs/tasks/18_deployment.md](docs/tasks/18_deployment.md)

---

## 📈 Performance Monitoring

View logs:
```bash
# Real-time logs
tail -f logs/trading_bot.log

# Filter by level
grep "ERROR" logs/trading_bot.log
grep "Trade executed" logs/trading_bot.log
```

Key metrics tracked:
- Total return %
- Sharpe ratio
- Win rate
- Max drawdown
- Number of trades
- PnL per trade

### 🖥️ Web Dashboard (New)

Get a quick visual snapshot of your mock trading performance with the built-in dashboard.

```bash
# Install requirements if you haven't already
pip install -r requirements.txt

# Launch the dashboard (default http://localhost:5000)
python -m web.app
```

Features:
- Live account balance, available cash, and deployed capital
- Open position overview with mark prices and unrealized PnL
- Recent trade history pulled directly from the mock exchange state
- Auto-refreshing charts driven by the data saved in `data/mock_exchange_state.json`

---

## ⚠️ Risk Disclaimer

**THIS IS EXPERIMENTAL SOFTWARE. USE AT YOUR OWN RISK.**

- Start with paper trading only
- Never risk more than you can afford to lose
- AI decisions are not guaranteed to be profitable
- Crypto trading is highly volatile
- Past performance does not guarantee future results
- Always test thoroughly before using real money

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **AI:** Anthropic Claude, OpenAI GPT
- **Data:** CoinGecko API (free)
- **Analysis:** pandas, pandas-ta
- **Scheduling:** APScheduler
- **Config:** Pydantic
- **Logging:** Loguru

---

## 📝 Project Status

**Current Progress:** ~40% complete

- ✅ Infrastructure: Complete
- 🔄 AI Integration: Next
- ⏭️ Trading Engine: Pending
- ⏭️ Testing & Deployment: Pending

**Estimated Time to MVP:** 10-15 hours

---

## 🤝 Contributing

This is a personal project, but suggestions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

TBD

---

## 📞 Support

For questions or issues:
1. Check the [documentation](docs/)
2. Review [task guides](docs/tasks/)
3. Check logs for errors

---

**Built with ❤️ and AI**
