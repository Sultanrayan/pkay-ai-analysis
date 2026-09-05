"""Runtime wiring ("composition root").

Builds every collaborator the bot needs — HTTP client, cache, rate limiter,
storage, data manager and analysis runner — from a :class:`Settings` object
and exposes them as one :class:`Services` bag stored on ``bot_data``.

Degradation policy (so a chat stays usable during infra hiccups):
* PostgreSQL unreachable  -> in-memory storage (logged loudly)
* Redis unreachable       -> in-memory rate limiter + null cache
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from .analysis.runner import AnalysisRunner
from .config import Settings
from .data.cache import Cache, NullCache, RedisCache
from .data.manager import MarketDataManager
from .storage.ratelimit import MemoryRateLimiter, RateLimiter, RedisRateLimiter
from .storage.repository import InMemoryStorage, PostgresStorage, Storage

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Services:
    settings: Settings
    http: httpx.AsyncClient
    storage: Storage
    cache: Cache
    limiter: RateLimiter
    data_manager: MarketDataManager
    runner: AnalysisRunner
    redis: Any | None = None


async def build_services(settings: Settings) -> Services:
    """Create all runtime dependencies from ``settings``."""
    http = httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True)

    redis = None
    try:
        import redis.asyncio as aioredis

        redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await redis.ping()
    except Exception as exc:
        logger.warning("Redis unreachable (%s); falling back to in-memory cache/limiter", exc)
        redis = None

    cache: Cache = RedisCache(redis) if redis is not None else NullCache()
    limiter: RateLimiter = (
        RedisRateLimiter(redis) if redis is not None else MemoryRateLimiter()
    )

    storage: Storage
    try:
        postgres = PostgresStorage(settings.database_url)
        await postgres.connect()
        storage = postgres
    except Exception as exc:
        logger.warning(
            "PostgreSQL unreachable (%s); using in-memory storage (data lost on restart)",
            exc,
        )
        storage = InMemoryStorage()
        await storage.connect()

    data_manager = MarketDataManager(http, settings, cache=cache)
    runner = AnalysisRunner(data_manager)
    return Services(
        settings=settings,
        http=http,
        storage=storage,
        cache=cache,
        limiter=limiter,
        data_manager=data_manager,
        runner=runner,
        redis=redis,
    )


async def close_services(services: Services) -> None:
    """Release HTTP connections, Redis and database pools."""
    await services.http.aclose()
    if services.redis is not None:
        try:
            await services.redis.aclose()
        except Exception:
            logger.debug("Redis close failed (ignored)", exc_info=True)
    try:
        await services.storage.close()
    except Exception:
        logger.debug("Storage close failed (ignored)", exc_info=True)
