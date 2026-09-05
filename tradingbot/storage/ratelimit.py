"""Daily per-user rate limiting.

A fixed daily window (UTC): each analysis request consumes one unit and the
limit resets at midnight UTC. The Redis implementation is authoritative in
production; the in-memory one powers tests and a graceful offline fallback.
Both share the :class:`RateLimiter` protocol.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

logger = logging.getLogger(__name__)


def _daily_key(user_id: int) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"tradingbot:rate:{user_id}:{today}"


def _seconds_until_midnight_utc() -> int:
    now = datetime.now(timezone.utc)
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((midnight - now).total_seconds()))


@dataclass(frozen=True, slots=True)
class RateLimitStatus:
    allowed: bool
    remaining: int
    limit: int
    reset_in_seconds: int


class RateLimiter(Protocol):
    """Consumes one request unit per call and reports the allowance."""

    async def consume(self, user_id: int, limit: int) -> RateLimitStatus: ...


class RedisRateLimiter:
    """Fixed daily window implemented with INCR + EXPIRE."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def consume(self, user_id: int, limit: int) -> RateLimitStatus:
        key = _daily_key(user_id)
        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            count, ttl = await pipe.execute()
            if int(ttl or 0) <= 0:
                await self._client.expire(key, _seconds_until_midnight_utc())
                ttl = _seconds_until_midnight_utc()
        except Exception:  # pragma: no cover - defensive against outages
            logger.warning("Redis rate limiter unavailable; allowing request")
            return RateLimitStatus(allowed=True, remaining=1, limit=limit, reset_in_seconds=0)
        count = int(count)
        return RateLimitStatus(
            allowed=count <= limit,
            remaining=max(0, limit - count),
            limit=limit,
            reset_in_seconds=int(ttl),
        )


class MemoryRateLimiter:
    """Process-local fixed daily window (tests / offline fallback)."""

    def __init__(self) -> None:
        self._counts: dict[int, tuple[str, int]] = {}

    async def consume(self, user_id: int, limit: int) -> RateLimitStatus:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stored = self._counts.get(user_id)
        count = 1
        if stored is not None:
            day, previous = stored
            count = previous + 1 if day == today else 1
        self._counts[user_id] = (today, count)
        return RateLimitStatus(
            allowed=count <= limit,
            remaining=max(0, limit - count),
            limit=limit,
            reset_in_seconds=_seconds_until_midnight_utc(),
        )
