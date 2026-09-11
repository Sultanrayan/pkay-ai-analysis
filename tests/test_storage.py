"""Tests for the in-memory storage backend and daily rate limiter."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from tradingbot.domain import Symbol, Timeframe
from tradingbot.storage.models import HistoryRow
from tradingbot.storage.ratelimit import MemoryRateLimiter
from tradingbot.storage.repository import InMemoryStorage


@pytest.mark.asyncio
async def test_user_creation_is_idempotent():
    storage = InMemoryStorage()
    first = await storage.get_or_create_user(42, username="alice", language_code="kh")
    second = await storage.get_or_create_user(42, username="alice", language_code="kh")
    assert first.user_id == second.user_id == 42
    assert second.language == "kh"


@pytest.mark.asyncio
async def test_preferences_defaults_and_updates():
    storage = InMemoryStorage()
    await storage.get_or_create_user(7)
    prefs = await storage.get_preferences(7)
    assert prefs.default_symbol == Symbol.BTCUSDT
    assert prefs.show_chart is True

    updated = await storage.update_preferences(7, default_symbol="XAUUSD", show_chart=False)
    assert updated.default_symbol == Symbol.XAUUSD
    assert updated.show_chart is False
    assert (await storage.get_preferences(7)).default_symbol == Symbol.XAUUSD


@pytest.mark.asyncio
async def test_history_roundtrip_ordering_and_ownership():
    storage = InMemoryStorage()
    await storage.get_or_create_user(1)
    await storage.get_or_create_user(2)

    def row_for(user: int, symbol: Symbol, when: datetime) -> HistoryRow:
        return HistoryRow(
            id=None, user_id=user, symbol=symbol.value, timeframe=Timeframe.H1.value,
            timestamp=when, current_price=100.0, technical_score=50, sentiment_score=0,
            risk_score=0, correlation_score=0, total_score=50, signal="BUY",
            summary="test", response_time_ms=12,
        )

    base = datetime(2026, 5, 1, tzinfo=timezone.utc)
    id_old = await storage.add_analysis(row_for(1, Symbol.BTCUSDT, base))
    id_new = await storage.add_analysis(row_for(1, Symbol.XAUUSD, base.replace(day=2)))
    await storage.add_analysis(row_for(2, Symbol.BTCUSDT, base.replace(day=3)))

    history = await storage.list_history(1)
    assert [r.id for r in history] == [id_new, id_old]  # newest first
    assert all(r.user_id == 1 for r in history)

    detail = await storage.get_history_row(1, id_old)
    assert detail is not None and detail.symbol == "BTCUSDT"
    # Ownership enforced: user 2 cannot read user 1's row.
    assert await storage.get_history_row(2, id_old) is None


@pytest.mark.asyncio
async def test_set_analysis_message_id():
    storage = InMemoryStorage()
    await storage.get_or_create_user(1)
    row = HistoryRow(
        id=None, user_id=1, symbol="BTCUSD", timeframe="1h",
        timestamp=datetime.now(timezone.utc), current_price=1.0,
        technical_score=0, sentiment_score=0, risk_score=0, correlation_score=0,
        total_score=0, signal="HOLD",
    )
    row_id = await storage.add_analysis(row)
    await storage.set_analysis_message_id(row_id, 555)
    assert (await storage.get_history_row(1, row_id)).message_id == 555


@pytest.mark.asyncio
async def test_memory_rate_limiter_window():
    limiter = MemoryRateLimiter()
    assert (await limiter.consume(1, limit=2)).allowed
    assert (await limiter.consume(1, limit=2)).allowed
    blocked = await limiter.consume(1, limit=2)
    assert not blocked.allowed
    assert blocked.remaining == 0
    # A different user is unaffected.
    assert (await limiter.consume(2, limit=2)).allowed


@pytest.mark.asyncio
async def test_memory_rate_limiter_resets_daily(monkeypatch):
    from datetime import datetime as _dt
    from datetime import timedelta as _td
    from datetime import timezone as _tz

    limiter = MemoryRateLimiter()
    # Force a specific UTC date for the first call.
    fixed = _dt(2026, 1, 1, 12, 0, tzinfo=_tz.utc)
    monkeypatch.setattr("tradingbot.storage.ratelimit.datetime", _FixedDate(fixed))
    assert (await limiter.consume(9, limit=1)).allowed
    assert not (await limiter.consume(9, limit=1)).allowed

    # Next UTC day -> counter resets.
    next_day = fixed + _td(days=1)
    monkeypatch.setattr("tradingbot.storage.ratelimit.datetime", _FixedDate(next_day))
    assert (await limiter.consume(9, limit=1)).allowed


class _FixedDate:
    """Stand-in for datetime that always returns a fixed 'now'."""

    def __init__(self, now) -> None:
        self._now = now

    def now(self, tz=None):
        return self._now.astimezone(tz) if tz else self._now
