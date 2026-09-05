# Contributing to Trading Analysis Bot

Thanks for your interest in contributing! This guide covers how to set up the
project, keep the code consistent, and where to look when extending it.

## Table of Contents

- [Getting Started](#getting-started)
- [Code Style & Quality](#code-style--quality)
- [Testing](#testing)
- [Extending the Project](#extending-the-project)
- [Git Workflow](#git-workflow)
- [Reporting Issues](#reporting-issues)

---

## Getting Started

1. **Clone and install**

   ```bash
   git clone https://github.com/Sultanrayan/pkay-ai-analysis.git
   cd pkay-ai-analysis
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

   `requirements-dev.txt` includes the runtime dependencies plus the test
   tooling (`pytest`, `pytest-asyncio`) and `ruff`.

2. **Run the test suite**

   ```bash
   python -m pytest tests/
   ```

   Every test runs offline: market data tests use the deterministic demo
   provider and parse fixtures, so you never need API keys or infrastructure
   to verify a change.

3. **Run the bot (optional)**

   ```bash
   docker compose up -d            # PostgreSQL + Redis (optional but recommended)
   cp .env.example .env            # add TELEGRAM_BOT_TOKEN
   python scripts/init_db.py
   python bot.py
   ```

   If you leave `USE_DEMO_DATA=true` (or simply no keys at all), the bot runs
   end-to-end with simulated data.

---

## Code Style & Quality

- **Lint:** the project uses [ruff](https://docs.astral.sh/ruff/) with the
  ruleset configured in `pyproject.toml` (`E, F, I, UP, B, RUF, ISC`,
  line length 120).

  ```bash
  ruff check tradingbot scripts bot.py webhook_server.py tests
  ```

  Keep the linter clean on every pull request. The most common gotcha is
  that blank `except` clauses must be justified with a `# noqa: BLE001 -
  <reason>` comment when intentionally swallowing errors.

- **Type hints:** all public functions are annotated (Python 3.10+ union
  syntax, `from __future__ import annotations`). Prefer `| None` over
  `Optional`.

- **Imports:** sorted by `ruff --fix`; imports that are only used for type
  annotations go under `if TYPE_CHECKING:`.

- **Docstrings:** modules, classes and non-trivial functions should carry a
  short docstring explaining *why* something exists or how a formula is
  derived (see `tradingbot/indicators.py` and `tradingbot/agents/`).

- **Never commit secrets:** `.env`, tokens and API keys stay out of the repo
  (see `.gitignore`). New configuration goes through `tradingbot/config.py`
  and is documented in `.env.example`.

---

## Testing

- Tests live in `tests/` mirroring the package layout
  (`test_indicators.py`, `test_agents.py`, `test_data.py`, ...).
- `tests/conftest.py` provides deterministic candle fixtures
  (`make_candles(...)`).
- Async tests use `pytest-asyncio` (auto mode, no decorators needed).
- **Rule of thumb:** new pure logic (indicators, agents, parsing, formatting)
  needs unit tests; new integrations (providers, storage) need at least
  parser/fallback coverage with fixtures, never real network calls.

Run the suite with:

```bash
python -m pytest tests/ -q
```

---

## Extending the Project

The architecture is intentionally layered behind small protocols, so most
extensions touch one file.

| Task | Where to look |
|------|---------------|
| Add a trading pair | `tradingbot/domain.py` (Symbol), then the provider symbol maps in `tradingbot/data/providers.py` and any sentiment feed in `tradingbot/config.py` |
| Add a data source | implement the `CandleProvider` protocol in `tradingbot/data/providers.py` (or the news equivalent in `tradingbot/data/news.py`) and add it to the chain in `tradingbot/data/manager.py` |
| Add an analysis agent | create `tradingbot/agents/<name>.py` returning a result dataclass from `tradingbot/agents/base.py`, wire it into the runner (`tradingbot/analysis/runner.py`), and adjust weights in `tradingbot/agents/decision.py` |
| Change the signal weights | constants `WEIGHTS` in `tradingbot/agents/decision.py` (documented in the README) |
| Add a storage backend | implement the `Storage` protocol in `tradingbot/storage/repository.py` (see `InMemoryStorage`) |
| Change rate limiting | `tradingbot/storage/ratelimit.py` (`RateLimiter` protocol) |
| Add a language | add a `"xx"` dictionary to `STRINGS` in `tradingbot/telegram/i18n.py` (key sets must match `"en"` — there is a test for this) |
| Add a Telegram flow | extend the callback vocabulary in `tradingbot/telegram/callback_data.py` and register a handler in `tradingbot/telegram/handlers/` |

When in doubt, follow the existing file — each module has one job and its
name says what it does.

---

## Git Workflow

1. Create a branch off `main`:

   ```bash
   git checkout -b feat/my-change
   ```

2. Make focused commits. Commit messages should have a concise subject line
   (imperative mood) and, when needed, a short body explaining *why*:

   ```
   Fix Mermaid diagram syntax in README so all diagrams render

   Three diagrams failed to parse: mixed quoted/unquoted edge labels and
   parallelogram nodes that were never closed. Validated with mermaid.ink.
   ```

3. Run the checks before opening a pull request:

   ```bash
   ruff check tradingbot scripts bot.py webhook_server.py tests
   python -m pytest tests/ -q
   ```

4. Open a pull request against `main`. Describe what changed and why, and
   mention any tests you added. Small, reviewable PRs are preferred.

---

## Reporting Issues

Open an issue with:

- the command or button that triggered the problem,
- the expected vs. actual behaviour,
- the `LOG_LEVEL=DEBUG` output if the bot crashes (redact tokens!),
- whether it happened with live or demo data (`USE_DEMO_DATA`),
- your environment (OS, Python version).

Thanks again for contributing! 💛