# Trading Analysis Bot V3 — Multi-Asset AI (Telegram Bot)

## Overview

A **Telegram-based multi-asset trading analysis bot** that delivers on-demand,
multi-agent analysis for **BTCUSDT, ETHUSDT, SOLUSDT** and **XAUUSD**, plus a
**signal-only memecoin sniper** scan. Users interact directly with a Telegram
bot — type a command or tap a button to get a comprehensive trading report.

The bot uses **10 specialized AI agents** grouped into teams — technical,
market intelligence and risk — whose consensus drives the signal, with
optional **DeepSeek-V4-Flash** enrichment for the final call. Everything is
built to be clean, testable and honest about its data provenance (demo vs
live).

> **V3 roadmap:** the full enterprise spec (KMS, RabbitMQ, InfluxDB/Grafana,
> live on-chain feeds, order execution) lives in
> [`research/research_v3.md`](research/research_v3.md). This repository
> implements the core V3 upgrade; the sniper is **signal-only** and never
> places orders.

---

## Key Features

- **Multi-Asset** – BTCUSDT, ETHUSDT, SOLUSDT, XAUUSD (+ "All" analyses)
- **10 Specialized Agents** – technical, volume, volatility, pattern,
  sentiment, on-chain, macro, risk, correlation, sniper
- **DeepSeek-V4-Flash Enrichment** – optional LLM final signal with graceful
  fallback to the deterministic engine
- **Signal-Only Memecoin Sniper** – opportunity ranking + safety checks,
  never executes trades
- **On-Demand Analysis** – runs only when you ask (`/analyze ETHUSDT 4h`)
- **Interactive UI** – inline keyboards, rich formatting, candlestick charts
- **Multi-Language** – Khmer & English interfaces
- **Cross-Asset Correlation** – BTC↔XAU and ETH↔SOL return correlation
- **Risk Management** – ATR-based stops, take-profit and position sizing
- **Rate Limiting** – daily per-user analysis cap (Redis or in-memory)
- **Resilient Data** – live APIs (Binance/Yahoo/RSS/Fear&Greed) with a
  deterministic demo fallback so a chat always stays usable

---

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "User Layer"
        U[User]
        TG[Telegram App]
    end

    subgraph "Telegram Layer"
        WEBHOOK[Telegram Webhook]
        BOT[Bot Handler]
        CMD[Command Parser]
        CALLBACK[Callback Query Handler]
    end

    subgraph "Processing Layer"
        DM[Data Manager]
        ORCH[Analysis Runner]
        LLM[DeepSeek-V4-Flash]
        FORM[Message Formatter]
    end

    subgraph "Agent Layer"
        TA[Technical Team<br/>technical · volume · volatility · pattern]
        MI[Market Intel Team<br/>sentiment · on-chain · macro · correlation]
        RM[Risk Agent]
        SN[Sniper Agent<br/>signal-only]
        DE[Decision Engine]
    end

    subgraph "Data Layer"
        PF[Binance / Yahoo Price Feed]
        NF[News / Fear&Greed]
        SIM[Simulated Sources<br/>on-chain · macro · sniper]
        DB[(PostgreSQL)]
        CACHE[(Redis Cache)]
    end

    subgraph "Response Layer"
        MSG[Formatted Message]
        KEYBOARD[Inline Keyboard]
        IMG[Chart Image]
    end

    U -->|"/analyze"| TG
    TG --> WEBHOOK
    WEBHOOK --> BOT
    BOT --> CMD
    BOT --> CALLBACK

    CMD --> ORCH
    CALLBACK --> ORCH
    ORCH --> DM

    DM -->|Candles| PF
    DM -->|Sentiment| NF
    DM -->|Heuristics| SIM
    DM --> DB
    DM --> CACHE

    DM --> TA
    DM --> MI
    DM --> RM
    DM --> SN

    TA --> DE
    MI --> DE
    RM --> DE
    DE --> LLM
    LLM --> FORM
    DE --> FORM
    FORM --> MSG
    FORM --> KEYBOARD
    FORM --> IMG

    MSG --> TG
    KEYBOARD --> TG
    IMG --> TG
    TG --> U
```

### Multi-Agent System

| Team | Weight | Agents |
|------|--------|--------|
| **Technical** | 35% | `technical` (trend & momentum) · `volume` (OBV) · `volatility` (Bollinger) · `pattern` (breakouts) |
| **Market Intel** | 25% | `sentiment` (news & Fear&Greed) · `onchain` (whale/flows) · `macro` (rates/DXY/inflation) · `correlation` (BTC↔XAU, ETH↔SOL) |
| **Risk** | 20% | `risk` (ATR stops, position sizing) |
| **Sniper** | — (informational) | `sniper` — signal-only memecoin scan, never executes |

The directional signal is the team-weighted consensus (technical 0.35 +
market intel 0.25 + risk 0.20, normalized to /100). `confidence` is derived
from how strongly and unanimously the agents agree. The sniper block is
reported separately: opportunities and their safety profile, with a clear
"no orders are ever placed" disclaimer.

### Agent Signal Generation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator (Runner)
    participant T as Technical Team (4 agents)
    participant M as Market Intel (4 agents)
    participant R as Risk Agent
    participant S as Sniper Agent
    participant D as Decision Engine
    participant L as DeepSeek-V4-Flash (optional)

    U->>O: /analyze ETHUSDT 1h
    O->>O: Fetch candles, sentiment, on-chain, macro, sniper scan

    par Agent Execution
        O->>T: Analyze technicals (4 agents)
        T-->>O: Scores + reasoning
        O->>M: Gather market intel (4 agents)
        M-->>O: Scores + reasoning
        O->>R: Risk assessment
        R-->>O: SL/TP + position size
        O->>S: Memecoin scan (signal-only)
        S-->>O: Opportunity + safety scores
    end

    O->>D: Weighted consensus
    D-->>O: Signal + confidence + summary
    O->>L: Enrich final call (if configured)
    L-->>O: AI signal/summary or None (fallback)
    O-->>U: Complete report
```

---

## Telegram Bot Flow

```mermaid
flowchart TD
    START([User Opens Telegram]) --> START_CMD[Sends /start]
    START_CMD --> WELCOME[Welcome Message + Main Menu]

    WELCOME --> MENU{User Action}

    MENU -->|"Analyze"| SELECT[Select Asset]
    MENU -->|"Sniper"| SNIPER[Memecoin Scan]
    MENU -->|"History"| HISTORY[Show Past Analysis]
    MENU -->|"Settings"| SETTINGS[User Preferences]
    MENU -->|"Help"| HELP[Help Guide]

    SELECT --> SELECT_ASSET{Choose Asset}
    SELECT_ASSET -->|BTCUSDT| TIMEFRAME
    SELECT_ASSET -->|ETHUSDT| TIMEFRAME
    SELECT_ASSET -->|SOLUSDT| TIMEFRAME
    SELECT_ASSET -->|XAUUSD| TIMEFRAME
    SELECT_ASSET -->|All| TIMEFRAME
    SELECT_ASSET -->|Memecoin| SNIPER

    TIMEFRAME -->|1H / 4H / 1D / 1W| ANALYZE[Run Analysis]
    ANALYZE --> FETCH[Fetch Data]
    FETCH --> PROCESS[Run 10 Agents]
    PROCESS --> DECIDE[Decision Engine + LLM]
    DECIDE --> GEN_REPORT[Generate Report]

    GEN_REPORT --> DISPLAY[Display Formatted Report]
    DISPLAY --> BUTTONS[Action Buttons]
    BUTTONS --> ACTION{User Action}
    ACTION -->|"Refresh"| ANALYZE
    ACTION -->|"Export"| EXPORT[Send CSV]
    ACTION -->|"Sniper"| SNIPER
    ACTION -->|"History"| HISTORY
    ACTION -->|"Main Menu"| WELCOME

    HISTORY --> SHOW_HIST[Show Last 10 Analyses]
    SNIPER --> SNIPER_REPORT[Opportunities + Safety]
```

---

## Bot Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start the bot and show main menu | `/start` |
| `/analyze` | Begin analysis workflow | `/analyze` or `/analyze ETHUSDT 4h` or `/analyze all 1d` |
| `/sniper` | Memecoin scan (signal-only, never places orders) | `/sniper` |
| `/history` | View your analysis history | `/history` |
| `/settings` | Configure bot preferences | `/settings` |
| `/help` | Show help guide | `/help` |
| `/about` | Bot information | `/about` |
| `/cancel` | Cancel current operation | `/cancel` |

---

## Sample Report

```
📊 BTCUSDT Analysis Report
Time: 08/09/2026 14:30 UTC · Timeframe: 1H
🤖 AI-enhanced (DeepSeek-V4-Flash)
━━━━━━━━━━━━━━━━━━━━━
💰 Current Price: $64,120.50
Signal: 🟢 BUY (Score: +58/100 · Confidence: 82%)

━━━━━━━━━━━━━━━━━━━━━
🤝 Agent Consensus (4 teams)
📈 Technical Indicators: ████████░░ 78% (+58.0)
💬 Market Sentiment:     ██████░░░░ 62% (+24.0)
🛡️ Risk Management:      ███████░░░ 70% (+40.0)
🎯 Sniper Scan:          ███░░░░░░░ 31% (Opportunity)

━━━━━━━━━━━━━━━━━━━━━
📈 Technical Indicators
• RSI (14): 58.4
• MACD: 0.0034
• MA 50: $63,900
• MA 200: $62,400
• Volume: 1.35x avg
• OBV trend: +18
• Volatility: 2.1% band · Band squeeze
• Pattern: bullish
• Support: $63,200
• Resistance: $65,100

━━━━━━━━━━━━━━━━━━━━━
💬 Market Sentiment
• News: +12.0 (8 headlines)
• Fear & Greed: 64 (Greed)
• Social Volume: 1,240

━━━━━━━━━━━━━━━━━━━━━
⛓ On-Chain
• Whale activity: +42.0
• Exchange netflow: +28.0
• Active addresses: +15.0
• MVRV: 2.10
• SOPR: 1.050

━━━━━━━━━━━━━━━━━━━━━
🌐 Macro
• Rate policy: +30
• DXY (dollar): -20
• Inflation: +40

━━━━━━━━━━━━━━━━━━━━━
🛡️ Risk Management
• Stop Loss: $62,900 (-1.9%)
• Take Profit: $66,100 (+3.1%)
• Position Size: 2.5%
• Volatility: 1.4% (Medium)
• ATR (14): 890.00

━━━━━━━━━━━━━━━━━━━━━
🔗 Correlation
• Correlation (r): r = -0.12 (XAUUSD)
  low correlation (r=-0.12) — assets behave independently

━━━━━━━━━━━━━━━━━━━━━
🎯 Sniper Scan
• Opportunity: 31/100 · Safety 92/100
• PEPE_X (solana): Liquidity $2,100,000 · Hype 85 · Safety 92 · +18.4%
ℹ️ Signal-only detection — no orders are ever placed.

━━━━━━━━━━━━━━━━━━━━━
📝 Summary
Technical view is bullish (RSI 58.4), price above the 50-period average.
News sentiment +12.0, Fear & Greed 64 (Greed). On-chain flows are
heuristic (simulated) in this build. Macro backdrop risk-on (simulated
values). Volatility 1.40%/candle (Medium); suggested stop at 62,900 and
target at 66,100 with ~2.5% position. Correlation with XAUUSD is
r=-0.12 (+12.0/100 contribution). Signal is BUY with total score +58.0/100.

[🔄 Refresh] [📄 Export] [🎯 Sniper] [🕘 History] [🏠 Main Menu]
```

---

## Database Schema

```mermaid
erDiagram
    TELEGRAM_USERS ||--o{ ANALYSIS_HISTORY : performs
    TELEGRAM_USERS ||--|| USER_PREFERENCES : has

    TELEGRAM_USERS {
        bigint user_id PK
        string username
        string language_code "kh/en"
        int daily_requests
        date last_request_date
        int max_daily_requests "default: 10"
        boolean is_premium
        datetime created_at
        datetime last_active
    }

    ANALYSIS_HISTORY {
        int id PK
        bigint user_id FK
        string symbol
        string timeframe
        datetime timestamp
        decimal current_price
        int technical_score
        int volume_score
        int volatility_score
        int pattern_score
        int sentiment_score
        int onchain_score
        int macro_score
        int risk_score
        int correlation_score
        int sniper_score
        int total_score
        decimal confidence
        string signal
        decimal rsi
        decimal ma_50
        decimal ma_200
        decimal support
        decimal resistance
        decimal stop_loss
        decimal take_profit
        decimal position_size_pct
        decimal atr
        text summary
        string chart_url
        int response_time_ms
        bigint message_id
        boolean llm_enhanced
        jsonb agent_contributions
    }

    USER_PREFERENCES {
        bigint user_id PK
        string default_symbol "BTCUSDT"
        string default_timeframe "1h"
        boolean show_chart "true"
        boolean show_indicators "true"
        boolean show_risk "true"
        boolean show_sentiment "true"
        string notification_enabled "daily"
        datetime updated_at
    }
```

The schema lives in `tradingbot/storage/schema.sql`. Existing databases are
migrated automatically at startup with idempotent `ADD COLUMN IF NOT EXISTS`
statements, so upgrading from v2 keeps your history.

---

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 13+ (optional at runtime — in-memory fallback)
- Redis 6+ (optional at runtime — in-memory fallback)
- Telegram Bot Token (from @BotFather)
- DeepSeek API Key (optional — enables AI-enriched signals)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Sultanrayan/pkay-ai-analysis.git
cd pkay-ai-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (production stack)
docker compose up -d

# Configure environment variables
cp .env.example .env
# Edit .env with your Telegram Bot Token (and optionally DEEPSEEK_API_KEY)

# Initialize database (idempotent; can be re-run safely)
python scripts/init_db.py

# Run bot (development with polling)
python bot.py

# Run with webhook (production)
python webhook_server.py

# Register the webhook with Telegram (after deploying behind HTTPS)
python scripts/set_webhook.py --url https://your-domain.com/webhook
```

> **No keys? No problem.** The bot ships with a deterministic *demo* data
> provider. Set `USE_DEMO_DATA=true` (or leave `DEMO_FALLBACK=true`, the
> default) and it runs end-to-end offline with simulated candles and
> sentiment, clearly flagged in the reports. When the live free APIs
> (Binance public, Yahoo Finance, RSS news, Fear & Greed index) are
> reachable they are used automatically; any failure falls back to demo
> data so a chat stays usable. On-chain, macro and sniper data are served
> by clearly-flagged heuristic sources unless live provider keys are wired.
> PostgreSQL/Redis are optional at runtime — the bot degrades to in-memory
> storage and rate limiting when they are unreachable.

### Environment Variables (.env)

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook

# Webhook Security
WEBHOOK_SECRET=your_secret_here

# Database
DATABASE_URL=postgresql://user:password@localhost/trading_bot
REDIS_URL=redis://localhost:6379/0

# Bot Settings
DEFAULT_SYMBOL=BTCUSDT
DEFAULT_TIMEFRAME=1h
MAX_DAILY_REQUESTS=10
LOG_LEVEL=INFO

# DeepSeek-V4-Flash (optional AI enrichment; deterministic fallback built-in)
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_TIMEOUT_SECONDS=20

# Signal-only memecoin sniper (never executes orders)
SNIPER_ENABLED=true
SNIPER_MIN_LIQUIDITY=500000
SNIPER_MAX_OPPORTUNITIES=3

# Chart Generation
CHART_ENABLED=true
CHART_PATH=/tmp/charts/

# Data Sources
USE_DEMO_DATA=false
DEMO_FALLBACK=true
```

---

## Repository Layout

```
bot.py                       # Dev entry point (long polling)
webhook_server.py            # Production entry point (webhook)
docker-compose.yml           # PostgreSQL 16 + Redis 7 for local development
scripts/                     # init_db.py, set_webhook.py, load_test.py
research/research_v3.md      # V3 specification / roadmap

tradingbot/
├── config.py                # Settings from .env (single configuration object)
├── domain.py                # Shared models: Symbol, Timeframe, Candle, snapshots
├── indicators.py            # Dependency-free indicator math (RSI, MACD, ATR, ...)
├── services.py              # Composition root (wires data/storage/cache/limiter/llm)
├── application.py           # Shared Telegram Application assembly
├── llm.py                   # DeepSeek-V4-Flash client (graceful fallback)
├── charts.py                # Pillow candlestick chart renderer
├── exporter.py              # CSV export of analysis history
├── webhook_security.py      # Telegram webhook signature verification
├── data/                    # Market data: Binance/Yahoo providers + demo fallback,
│   │                        #   RSS/Fear&Greed sentiment, simulated on-chain/macro/
│   │                        #   sniper sources, Redis/Null cache
├── agents/                  # 10 agents + decision engine (see agents/__init__.py)
├── analysis/                # Runner orchestrating the agents into a report
├── storage/                 # Postgres (asyncpg) + in-memory repositories, schema.sql,
│   │                        #   daily rate limiter (Redis or in-memory)
└── telegram/                # i18n (EN/KH), keyboards, HTML formatters, callback
                             #   data conventions, command/flow handlers

tests/                       # Pytest suite (run with: python -m pytest tests/)
```

Each layer talks to the next through small protocols/interfaces, so new
providers, agents, symbols or storage backends can be added without touching
callers. Agents are pure functions of their inputs and every indicator has
unit coverage.

---

## Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Lint
ruff check .
```

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

---

## Contact & Support

- **Telegram:** [Developer](https://t.me/spcaeechoo)
- **Email:** errorkruzer1@gmail.com
- **GitHub Issues:** [Open an Issue](https://github.com/Sultanrayan/pkay-ai-analysis/issues)

---

## Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [DeepSeek](https://platform.deepseek.com) - DeepSeek-V4-Flash LLM enrichment
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [Pillow](https://python-pillow.org/) - Chart image generation