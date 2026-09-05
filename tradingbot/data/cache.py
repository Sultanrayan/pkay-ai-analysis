"""Caching abstractions.

The rest of the code talks to the :class:`Cache` protocol so Redis can be
swapped for another store (or disabled) without touching callers.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class Cache(Protocol):
    """Async key/value cache used for price data."""

    async def get(self, key: str) -> Any | None: ...

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...


class NullCache:
    """No-op cache: every read misses, every write is dropped."""

    async def get(self, key: str) -> Any | None:
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        return None


class RedisCache:
    """JSON cache on top of a shared ``redis.asyncio`` client.

    Serialization is JSON so cached payloads stay interoperable across
    versions of the process. Redis outages degrade to cache misses — the
    caller falls back to a live fetch.
    """

    KEY_PREFIX = "tradingbot:cache:"

    def __init__(self, client: Any) -> None:
        self._client = client

    def _full_key(self, key: str) -> str:
        return f"{self.KEY_PREFIX}{key}"

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self._client.get(self._full_key(key))
        except Exception:  # pragma: no cover - defensive against outages
            logger.warning("Redis read failed for key %r; treating as miss", key)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        try:
            payload = json.dumps(value)
            if ttl_seconds is None:
                await self._client.set(self._full_key(key), payload)
            else:
                await self._client.set(self._full_key(key), payload, ex=ttl_seconds)
        except Exception:  # pragma: no cover - defensive against outages
            logger.warning("Redis write failed for key %r; skipping cache", key)
