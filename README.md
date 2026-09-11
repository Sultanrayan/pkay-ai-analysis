![Pkay AI](img-repo.jpg)

# Pkay AI — Multi-Asset AI Trading Analysis (Telegram Bot)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#mit-license)
[![Tests](https://img.shields.io/badge/tests-pytest-informational.svg)](#testing)

## Overview

**Pkay AI** is a **Telegram-based multi-asset trading analysis bot** that delivers
on-demand, multi-agent analysis for **BTCUSDT, ETHUSDT, SOLUSDT** and **XAUUSD**,
plus a **signal-only memecoin sniper** scan. Users interact directly with a
Telegram bot — type a command or tap a button to get a comprehensive trading
report.

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

Pkay AI is organized into six layers. Each layer only talks to the next
through small protocols, so providers, agents and storage backends can be
swapped without touching callers.

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **User** | Telegram App | Where the user sends commands and taps buttons |
| **Telegram** | Webhook / Bot Handler · Command Parser · Callback Handler | Receives updates, routes commands and inline callbacks |
| **Processing** | Data Manager · Analysis Runner · DeepSeek-V4-Flash · Formatter | Fetches data, orchestrates agents, formats the report |
| **Agent** | Technical Team · Market Intel Team · Risk · Sniper · Decision Engine | Produces scores and the weighted consensus signal |
| **Data** | Binance/Yahoo · News/Fear&Greed · Simulated sources · PostgreSQL · Redis | Live and fallback data, persistence and caching |
| **Response** | Formatted Message · Inline Keyboard · Chart Image | Delivers the final report back to Telegram |

**Request path:** `User → Telegram → Webhook → Bot Handler → Command/Callback →`
`Analysis Runner → Data Manager → Agents → Decision Engine → (optional LLM) →`
`Formatter → Message/Keyboard/Chart → Telegram → User`.

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

1. User sends `/analyze ETHUSDT 1h`.
2. The orchestrator fetches candles, sentiment, on-chain, macro and a sniper
   scan.
3. Agent teams run in parallel:
   - Technical team (4 agents) → scores + reasoning
   - Market intel team (4 agents) → scores + reasoning
   - Risk agent → SL/TP + position size
   - Sniper agent → opportunity + safety scores
4. The Decision Engine computes the weighted consensus → signal, confidence
   and summary.
5. DeepSeek-V4-Flash optionally enriches the final call (or `None` on any
   error, falling back to the deterministic result).
6. A complete report is returned to the user.

---

## Telegram Bot Flow

1. **User opens Telegram** and sends `/start`.
2. Bot replies with the **welcome message + main menu**.
3. From the menu the user can choose **Analyze**, **Sniper**, **History**,
   **Settings** or **Help**.
4. **Analyze** → choose asset (BTCUSDT / ETHUSDT / SOLUSDT / XAUUSD / All /
   Memecoin) → choose timeframe (1H / 4H / 1D / 1W) → analysis runs.
5. The bot fetches data, runs the 10 agents, applies the Decision Engine
   (+ optional LLM) and generates the report.
6. The formatted report is displayed with action buttons:
   **Refresh**, **Export**, **Sniper**, **History**, **Main Menu**.
7. **History** shows the last 10 analyses; **Sniper** shows opportunities and
   their safety profile.

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

The schema lives in `tradingbot/storage/schema.sql`. Existing databases are
migrated automatically at startup with idempotent `ADD COLUMN IF NOT EXISTS`
statements, so upgrading from v2 keeps your history.

**`TELEGRAM_USERS`** — one row per user (PK `user_id`):

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | bigint | primary key |
| `username` | string | |
| `language_code` | string | `kh` / `en` |
| `daily_requests` | int | |
| `last_request_date` | date | |
| `max_daily_requests` | int | default `10` |
| `is_premium` | boolean | |
| `created_at` | datetime | |
| `last_active` | datetime | |

**`ANALYSIS_HISTORY`** — many rows per user (PK `id`, FK `user_id`):

| Column | Type |
|--------|------|
| `id` | int (PK) |
| `user_id` | bigint (FK) |
| `symbol`, `timeframe`, `signal` | string |
| `timestamp` | datetime |
| `current_price` | decimal |
| `technical_score`, `volume_score`, `volatility_score`, `pattern_score` | int |
| `sentiment_score`, `onchain_score`, `macro_score`, `risk_score` | int |
| `correlation_score`, `sniper_score`, `total_score` | int |
| `confidence` | decimal |
| `rsi`, `ma_50`, `ma_200`, `support`, `resistance` | decimal |
| `stop_loss`, `take_profit`, `position_size_pct`, `atr` | decimal |
| `summary` | text |
| `chart_url` | string |
| `response_time_ms` | int |
| `message_id` | bigint |
| `llm_enhanced` | boolean |
| `agent_contributions` | jsonb |

**`USER_PREFERENCES`** — one row per user (PK `user_id`):

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | bigint | primary key |
| `default_symbol` | string | default `BTCUSDT` |
| `default_timeframe` | string | default `1h` |
| `show_chart`, `show_indicators`, `show_risk`, `show_sentiment` | boolean | |
| `notification_enabled` | string | default `daily` |
| `updated_at` | datetime | |

---

## Install Guide

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 13+** (optional at runtime — in-memory fallback)
- **Redis 6+** (optional at runtime — in-memory fallback)
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
- **DeepSeek API Key** (optional — enables AI-enriched signals)

### Step 1 — Clone the repository

```bash
git clone https://github.com/Sultanrayan/pkay-ai-analysis.git
cd pkay-ai-analysis
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Start the data stack (production)

```bash
docker compose up -d
```

This brings up PostgreSQL 16 and Redis 7. Both are optional — skip this step
and the bot degrades to in-memory storage and rate limiting.

### Step 5 — Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at least your `TELEGRAM_BOT_TOKEN`. Add
`DEEPSEEK_API_KEY` to enable AI-enriched signals. See
[Environment Variables](#environment-variables-env) for the full list.

### Step 6 — Initialize the database

```bash
python scripts/init_db.py
```

This is idempotent and safe to re-run.

### Step 7 — Run the bot

```bash
# Development (long polling)
python bot.py

# Production (webhook)
python webhook_server.py
```

### Step 8 — Register the webhook (production only)

After deploying behind HTTPS:

```bash
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

## MIT License

This project is licensed under the **MIT License** — see the
[LICENSE](LICENSE.md) file for the full text.

```
MIT License

Copyright (c) 2026 Pkay AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

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
