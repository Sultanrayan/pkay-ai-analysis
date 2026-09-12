![Pkay AI](img-repo.jpg)

# Pkay AI — Multi-Asset AI Trading Analysis (Website + API)

[![Website](https://img.shields.io/badge/website-developer.pkay.fun-blue.svg)](https://developer.pkay.fun)
[![API](https://img.shields.io/badge/api-auth.pkay.fun-green.svg)](https://auth.pkay.fun/health)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18-61dafb.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#mit-license)
[![Tests](https://img.shields.io/badge/tests-137%20passing-informational.svg)](#testing)

## Overview

**Pkay AI** is a **website and public API** for multi-asset trading analysis.
The site (`pkay_web`) gives users a marketing front-end, a **Google-authenticated
dashboard** for API keys and usage, live docs, and pricing. The API serves the
**AI Agent Team** behind two endpoints: `/api/v3/analyze` (built-in AI analysis)
and `/api/v3/agents` (callable function definitions for your own AI model).

Ten specialized agents — technical, market intelligence and risk — vote into one
weighted consensus, enriched by the latest AI model. Everything is built to be
clean, testable and honest about data provenance (demo vs live).

**Live**
- Website / dashboard: **https://developer.pkay.fun**
- API + Google sign-in: **https://auth.pkay.fun**

> The original Telegram bot is still in the repo (`bot.py`, `webhook_server.py`)
> as an optional channel, but the product is now the website + API.

---

## Key Features

**Website**
- **Google sign-in** — one-click login/registration (OAuth 2.0)
- **Dashboard** — create, revoke and delete API keys; usage analytics; playground
- **Everything from the database** — keys, usage, profile and preferences persist in PostgreSQL
- **Docs, pricing, how-it-works** — full marketing site with a live request playground
- **Settings** — language, currency, timezone, notifications, theme, API defaults
- **Multi-asset** — BTCUSDT, ETHUSDT, SOLUSDT, XAUUSD
- **Timeframes** — `1m · 5m · 15m · 1h · 4h · 1d · 1w`

**API**
- **`POST /api/v3/analyze`** — multi-agent analysis with built-in AI analysis
- **`POST /api/v3/agents`** — AI Agent Team function definitions (functions-only)
- **Key-scoped auth** — hashed API keys, per-request usage logging
- **10 specialized agents** with a weighted consensus
- **AI model enrichment** with graceful deterministic fallback
- **Signal-only memecoin sniper** — never executes orders
- **Risk management** — ATR-based stops, take-profit and position sizing

---

## System Architecture

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Website** | React · Vite · Tailwind CSS · React Router | Marketing pages, dashboard, docs, auth UI |
| **API** | aiohttp · Google OAuth · API keys · usage logging | Public JSON API and account endpoints |
| **Processing** | Data Manager · Analysis Runner · AI model · Serializer | Fetches data, orchestrates agents, builds the response |
| **Agents** | Technical Team · Market Intel Team · Risk · Sniper · Decision Engine | Scores and the weighted consensus |
| **Data** | Binance/Yahoo · News/Fear&Greed · Simulated sources | Live data with deterministic demo fallback |
| **Storage** | PostgreSQL · Redis (optional) | Accounts, keys, usage, history, cache, rate limiting |

**Request path:** `Browser → Website → API → Analysis Runner → Data Manager →`
`Agents → Decision Engine → (optional AI model) → JSON response`.

### Multi-Agent System

| Team | Weight | Agents |
|------|--------|--------|
| **Technical** | 35% | `technical` (trend & momentum) · `volume` (OBV) · `volatility` (Bollinger) · `pattern` (breakouts) |
| **Market Intel** | 25% | `sentiment` (news & Fear&Greed) · `onchain` (whale/flows) · `macro` (rates/DXY/inflation) · `correlation` (BTC↔XAU, ETH↔SOL) |
| **Risk** | 20% | `risk` (ATR stops, position sizing) |
| **Sniper** | — (informational) | `sniper` — signal-only memecoin scan, never executes |

The directional signal is the team-weighted consensus (technical 0.35 + market
intel 0.25 + risk 0.20, normalized to /100). `confidence` reflects how strongly
and unanimously the agents agree.

---

## Public API Reference

Base URL: **`https://auth.pkay.fun`**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v3/analyze` | Multi-agent analysis (built-in AI analysis) for a Data Pair |
| `POST` | `/api/v3/agents` | AI Agent Team function definitions (functions-only) |
| `GET` | `/api/v3/auth/google` | Start Google sign-in / registration |
| `GET` | `/api/v3/auth/google/callback` | OAuth callback — issues a session token |
| `GET` | `/api/v3/auth/me` | Current account (Bearer session token) |
| `GET` | `/api/v3/keys` | List the account's API keys |
| `POST` | `/api/v3/keys` | Create an API key (returns the secret once) |
| `POST` | `/api/v3/keys/{id}/revoke` | Revoke a key |
| `DELETE` | `/api/v3/keys/{id}` | Delete a key |
| `GET` | `/api/v3/usage?days=14` | Usage summary, daily series and breakdowns |
| `GET` | `/api/v3/settings` | Account preferences |
| `PUT` | `/api/v3/settings` | Update account preferences |
| `POST` | `/api/v3/auth/password` | Set / change the account password |
| `GET` | `/health` | Liveness probe |

### Analyze a Data Pair

```bash
curl -X POST https://auth.pkay.fun/api/v3/analyze \
  -H "Authorization: Bearer pk_live_xxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{ "symbol": "BTCUSDT", "timeframe": "15m" }'
```

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "signal": "BUY",
  "score": 58,
  "confidence": 82,
  "current_price": 64120.50,
  "agents": { "technical": 52.2, "sentiment": 29.0, "risk": 40.6, "...": 0 },
  "risk": { "stop_loss": 62900.0, "take_profit": 66100.0, "position_size_pct": 2.5 },
  "model": "deepseek-v4-flash",
  "llm_enhanced": true,
  "summary": "Technical momentum is bullish, price is above the 50-period average..."
}
```

### Agent functions

`POST /api/v3/agents` returns callable function definitions (tools) for the AI
Agent Team. It performs **no analysis** and does not accept a user model.

```bash
curl -X POST https://auth.pkay.fun/api/v3/agents \
  -H "Authorization: Bearer pk_live_xxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{ "functions": ["technical", "sentiment", "risk"], "format": "tools" }'
```

---

## Repository Layout

```
pkay_web/                    # React + Vite + Tailwind website & dashboard
├── src/
│   ├── pages/               # Home, How it works, Features, Pricing, Docs,
│   │                        #   Dashboard, About, Login
│   ├── components/          # Navbar, Footer, charts, dashboard widgets, settings
│   └── lib/                 # API client, models, agents, theme

tradingbot/                  # Python backend
├── api/                     # aiohttp app: /api/v3/*, OAuth, keys, usage, settings
│   ├── server.py            # routes, auth, CORS, dashboard endpoints
│   ├── oauth.py             # Google OAuth + session tokens
│   ├── agents.py            # AI Agent Team function catalogue
│   └── keys.py              # API key generation/hashing
├── agents/                  # 10 agents + decision engine
├── analysis/                # Runner orchestrating the agents into a report
├── data/                    # Binance/Yahoo providers, news, demo fallback, cache
├── storage/                 # PostgreSQL + in-memory repositories, schema.sql
└── telegram/                # optional Telegram channel (i18n, keyboards, handlers)

api_server.py                # Standalone JSON API entry point (no Telegram)
webhook_server.py            # Optional combined Telegram webhook + API
bot.py                       # Optional Telegram polling (development)
scripts/                     # init_db.py, set_webhook.py, load_test.py
```

---

## Install Guide

### Prerequisites

- **Node.js 20+** (website)
- **Python 3.10+** (API)
- **PostgreSQL 13+** (persists accounts, keys and usage; in-memory fallback otherwise)
- **Google OAuth client** (Client ID + Secret) for sign-in
- **Redis 6+** (optional — cache/rate limiting)

### 1. Clone

```bash
git clone https://github.com/Sultanrayan/pkay-ai-analysis.git
cd pkay-ai-analysis
```

### 2. Website

```bash
cd pkay_web
npm install
npm run dev        # http://localhost:5173
npm run build      # production build in dist/
```

Point the site at your API with `VITE_API_URL` (defaults to
`https://auth.pkay.fun`).

### 3. API

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Database

```bash
cp .env.example .env          # set DATABASE_URL and the Google credentials
python scripts/init_db.py     # idempotent — safe to re-run
```

### 5. Run the API

```bash
python api_server.py          # serves /api/v3/* and /health on $PORT
```

### Environment Variables (.env)

```env
# Database / cache
DATABASE_URL=postgresql://user:password@localhost:5432/trading_bot
REDIS_URL=redis://localhost:6379/0

# Public API keys (comma separated; empty = open in dev)
PKAY_API_KEYS=

# Google OAuth (sign-in / registration)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
AUTH_BASE_URL=https://auth.pkay.fun
FRONTEND_URL=https://developer.pkay.fun
SESSION_SECRET=generate-with-python-secrets
CORS_ORIGINS=https://developer.pkay.fun,http://localhost:5173

# AI model enrichment (optional; deterministic fallback built in)
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_TIMEOUT_SECONDS=20

# Bot defaults
DEFAULT_SYMBOL=BTCUSDT
DEFAULT_TIMEFRAME=1h
LOG_LEVEL=INFO
USE_DEMO_DATA=false
DEMO_FALLBACK=true

# Signal-only memecoin sniper (never executes orders)
SNIPER_ENABLED=true
SNIPER_MIN_LIQUIDITY=500000
SNIPER_MAX_OPPORTUNITIES=3

# Charts
CHART_ENABLED=true
CHART_PATH=./charts

# Optional Telegram channel
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_URL=
WEBHOOK_SECRET=
```

> **No keys? No problem.** The API ships with a deterministic *demo* data
> provider. With `USE_DEMO_DATA=true` (or the default `DEMO_FALLBACK=true`) it
> runs end-to-end offline with simulated candles and sentiment, clearly flagged
> in the responses. PostgreSQL/Redis are optional at runtime — the API degrades
> to in-memory storage and rate limiting.

---

## Deployment (Railway)

The project deploys as **two services** plus PostgreSQL:

| Service | Source | Notes |
|---------|--------|-------|
| `pkay-web` | `pkay_web/` (Dockerfile) | Static front-end at `developer.pkay.fun` |
| `pkay-gateway` | repo root (`api_server.py`) | API at `auth.pkay.fun` |
| `Postgres` | Railway database | Set `DATABASE_URL=${{Postgres.DATABASE_URL}}` |

```bash
# API (from the repo root)
railway up -s pkay-gateway

# Website (from pkay_web/)
railway up -s pkay-web
```

Register the Google OAuth redirect URI:
`https://auth.pkay.fun/api/v3/auth/google/callback`

---

## Testing

```bash
python -m pytest tests/     # 137 tests
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

- **Website:** [developer.pkay.fun](https://developer.pkay.fun)
- **Telegram:** [Developer](https://t.me/spcaeechoo)
- **Email:** errorkruzer1@gmail.com
- **GitHub Issues:** [Open an Issue](https://github.com/Sultanrayan/pkay-ai-analysis/issues)

---

## Acknowledgements

- [React](https://react.dev/) + [Vite](https://vite.dev/) + [Tailwind CSS](https://tailwindcss.com/) - website
- [aiohttp](https://docs.aiohttp.org/) - JSON API server
- [DeepSeek](https://platform.deepseek.com) - AI model enrichment
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - optional Telegram channel
- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [Pillow](https://python-pillow.org/) - Chart image generation
