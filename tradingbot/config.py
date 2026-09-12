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
#: DeepSeek chat-completions endpoint (OpenAI-compatible).
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
#: Sniper scan defaults (kept here so Settings defaults stay self-contained).
DEFAULT_SNIPER_MIN_LIQUIDITY = 500_000.0
DEFAULT_SNIPER_MAX_OPPORTUNITIES = 3

DEFAULT_NEWS_FEEDS: dict[Symbol, str] = {
    # Crypto-specific feed (covers all crypto majors).
    Symbol.BTCUSDT: "https://www.coindesk.com/arc/outboundfeeds/rss/",
    # Google News RSS aggregates reliable per-asset headlines (Kitco's own
    # RSS now serves an HTML app for gold; CoinDesk is BTC-only).
    Symbol.ETHUSDT: (
        "https://news.google.com/rss/search?q=ethereum+price&hl=en-US&gl=US&ceid=US:en"
    ),
    Symbol.SOLUSDT: (
        "https://news.google.com/rss/search?q=solana+price&hl=en-US&gl=US&ceid=US:en"
    ),
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

    # Public JSON API (v3). Comma-separated keys in PKAY_API_KEYS.
    # An empty tuple means the API is open (development only).
    api_keys: tuple[str, ...] = field(default_factory=tuple)

    # Google OAuth (public API sign-in / registration)
    google_client_id: str = ""
    google_client_secret: str = ""
    auth_base_url: str = "https://auth.pkay.fun"
    frontend_url: str = ""
    session_secret: str = ""

    # CORS: comma-separated allowed origins. Empty means allow any origin.
    cors_origins: tuple[str, ...] = field(default_factory=tuple)

    # Bot defaults
    default_symbol: Symbol = Symbol.BTCUSDT
    default_timeframe: Timeframe = Timeframe.H1
    max_daily_requests: int = 10
    log_level: str = "INFO"

    # Data sources
    use_demo_data: bool = False
    demo_fallback: bool = True
    fear_greed_api_url: str = DEFAULT_FEAR_GREED_URL
    news_rss_feeds: tuple[str, ...] = field(default_factory=tuple)
    candle_cache_ttl: int = 120  # seconds

    # DeepSeek-V4-Flash (optional LLM signal enrichment; the deterministic
    # decision engine always remains the fallback when disabled/unreachable).
    deepseek_api_key: str = ""
    deepseek_model: str = DEFAULT_DEEPSEEK_MODEL
    deepseek_base_url: str = DEFAULT_DEEPSEEK_BASE_URL
    deepseek_timeout: float = 20.0

    # Signal-only memecoin sniper (never executes orders).
    sniper_enabled: bool = True
    sniper_min_liquidity: float = DEFAULT_SNIPER_MIN_LIQUIDITY
    sniper_max_opportunities: int = DEFAULT_SNIPER_MAX_OPPORTUNITIES

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

        default_symbol = Symbol.parse(_first_env("DEFAULT_SYMBOL", "DEFAULT_ASSET")) or Symbol.BTCUSDT
        default_timeframe = (
            Timeframe.parse(_first_env("DEFAULT_TIMEFRAME", "DEFAULT_INTERVAL")) or Timeframe.H1
        )
        feeds = tuple(
            url.strip()
            for url in _first_env("NEWS_RSS_FEEDS").split(",")
            if url.strip()
        )
        api_keys = tuple(
            key.strip()
            for key in _first_env("PKAY_API_KEYS").split(",")
            if key.strip()
        )
        cors_origins = tuple(
            origin.strip().rstrip("/")
            for origin in _first_env("CORS_ORIGINS").split(",")
            if origin.strip()
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
        try:
            deepseek_timeout = float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "20"))
        except ValueError:
            deepseek_timeout = 20.0
        try:
            sniper_min_liquidity = float(os.getenv("SNIPER_MIN_LIQUIDITY", str(DEFAULT_SNIPER_MIN_LIQUIDITY)))
        except ValueError:
            sniper_min_liquidity = DEFAULT_SNIPER_MIN_LIQUIDITY
        try:
            sniper_max_opps = int(os.getenv("SNIPER_MAX_OPPORTUNITIES", str(DEFAULT_SNIPER_MAX_OPPORTUNITIES)))
        except ValueError:
            sniper_max_opps = DEFAULT_SNIPER_MAX_OPPORTUNITIES

        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_webhook_url=os.getenv("TELEGRAM_WEBHOOK_URL", ""),
            webhook_host=os.getenv("WEBHOOK_HOST", "0.0.0.0"),
            webhook_port=webhook_port,
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            redis_url=os.getenv("REDIS_URL", cls.redis_url),
            api_keys=api_keys,
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            auth_base_url=os.getenv("AUTH_BASE_URL", "https://auth.pkay.fun"),
            frontend_url=os.getenv("FRONTEND_URL", ""),
            session_secret=os.getenv("SESSION_SECRET", ""),
            cors_origins=cors_origins,
            default_symbol=default_symbol,
            default_timeframe=default_timeframe,
            max_daily_requests=max_requests,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            use_demo_data=_bool(os.getenv("USE_DEMO_DATA")),
            demo_fallback=_bool(os.getenv("DEMO_FALLBACK"), default=True),
            fear_greed_api_url=os.getenv("FEAR_GREED_API_URL", DEFAULT_FEAR_GREED_URL),
            news_rss_feeds=feeds,
            candle_cache_ttl=cache_ttl,
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).rstrip("/"),
            deepseek_timeout=deepseek_timeout,
            sniper_enabled=_bool(os.getenv("SNIPER_ENABLED"), default=True),
            sniper_min_liquidity=sniper_min_liquidity,
            sniper_max_opportunities=sniper_max_opps,
            chart_enabled=_bool(os.getenv("CHART_ENABLED"), default=True),
            chart_path=Path(os.getenv("CHART_PATH", "charts")),
        )

    def news_feed_for(self, symbol: Symbol) -> str:
        """Resolve the RSS feed URL for a symbol (env override wins)."""
        if self.news_rss_feeds:
            return self.news_rss_feeds[0]
        return DEFAULT_NEWS_FEEDS[symbol]

    @property
    def google_redirect_uri(self) -> str:
        """OAuth redirect URI registered with Google."""
        return (
            f"{self.auth_base_url.rstrip('/')}/api/v3/auth/google/callback"
        )


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging once with a consistent format."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
