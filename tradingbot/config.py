"""Application configuration.

Reads a ``.env`` file (see ``.env.example``) plus the process environment,
then exposes everything through a single frozen :class:`Settings` object.
Centralising configuration here means modules never touch ``os.environ``
themselves and the whole bot can be reconfigured for tests.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from .domain import Symbol, Timeframe

ENV_FILE = ".env"

DEFAULT_FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"
DEFAULT_NEWS_FEEDS: dict[Symbol, str] = {
    # Crypto-specific feed.
    Symbol.BTCUSD: "https://www.coindesk.com/arc/outboundfeeds/rss/",
    # Gold/prices search feed (Kitco's own RSS now serves an HTML app; Google
    # News RSS aggregates Kitco + Reuters + Yahoo gold headlines instead).
    Symbol.XAUUSD: (
        "https://news.google.com/rss/search?q=gold+price&hl=en-US&gl=US&ceid=US:en"
    ),
}
CHART_PATH_DEFAULT = Path("charts")


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _first_env(*names: str) -> str:
    """Return the first non-empty environment variable among ``names``."""
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""


@dataclass(frozen=True, slots=True)
class Settings:
    """All runtime settings, parsed from environment variables."""

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8443

    # Data storage
    database_url: str = "postgresql://tradingbot:tradingbot@localhost:5432/trading_bot"
    redis_url: str = "redis://localhost:6379/0"

    # Bot defaults
    default_symbol: Symbol = Symbol.BTCUSD
    default_timeframe: Timeframe = Timeframe.H1
    max_daily_requests: int = 10
    log_level: str = "INFO"

    # Data sources
    use_demo_data: bool = False
    demo_fallback: bool = True
    fear_greed_api_url: str = DEFAULT_FEAR_GREED_URL
    news_rss_feeds: tuple[str, ...] = field(default_factory=tuple)
    candle_cache_ttl: int = 120  # seconds

    # Charts
    chart_enabled: bool = True
    chart_path: Path = CHART_PATH_DEFAULT

    @classmethod
    def from_env(
        cls, env_file: str | os.PathLike[str] = ENV_FILE, *, override: bool = False
    ) -> Settings:
        """Load settings from ``.env`` (if present) plus the environment.

        Unknown or invalid enum values fall back to the defaults so a typo in
        ``.env`` never crashes the bot at startup. Pass ``override=True`` to
        let the .env file win over already-set environment variables (useful
        in tests).
        """
        load_dotenv(env_file, override=override)

        default_symbol = Symbol.parse(_first_env("DEFAULT_SYMBOL", "DEFAULT_ASSET")) or Symbol.BTCUSD
        default_timeframe = (
            Timeframe.parse(_first_env("DEFAULT_TIMEFRAME", "DEFAULT_INTERVAL")) or Timeframe.H1
        )
        feeds = tuple(
            url.strip()
            for url in _first_env("NEWS_RSS_FEEDS").split(",")
            if url.strip()
        )
        try:
            railway_port = os.getenv("PORT")
            webhook_port = int(os.getenv("WEBHOOK_PORT", railway_port or "8443"))
        except ValueError:
            webhook_port = 8443
        try:
            max_requests = int(os.getenv("MAX_DAILY_REQUESTS", "10"))
        except ValueError:
            max_requests = 10
        try:
            cache_ttl = int(os.getenv("CANDLE_CACHE_TTL", "120"))
        except ValueError:
            cache_ttl = 120

        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_webhook_url=os.getenv("TELEGRAM_WEBHOOK_URL", ""),
            webhook_host=os.getenv("WEBHOOK_HOST", "0.0.0.0"),
            webhook_port=webhook_port,
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            redis_url=os.getenv("REDIS_URL", cls.redis_url),
            default_symbol=default_symbol,
            default_timeframe=default_timeframe,
            max_daily_requests=max_requests,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            use_demo_data=_bool(os.getenv("USE_DEMO_DATA")),
            demo_fallback=_bool(os.getenv("DEMO_FALLBACK"), default=True),
            fear_greed_api_url=os.getenv("FEAR_GREED_API_URL", DEFAULT_FEAR_GREED_URL),
            news_rss_feeds=feeds,
            candle_cache_ttl=cache_ttl,
            chart_enabled=_bool(os.getenv("CHART_ENABLED"), default=True),
            chart_path=Path(os.getenv("CHART_PATH", "charts")),
        )

    def news_feed_for(self, symbol: Symbol) -> str:
        """Resolve the RSS feed URL for a symbol (env override wins)."""
        if self.news_rss_feeds:
            return self.news_rss_feeds[0]
        return DEFAULT_NEWS_FEEDS[symbol]


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging once with a consistent format."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
