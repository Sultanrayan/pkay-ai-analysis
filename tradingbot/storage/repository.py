"""Persistence layer.

The bot talks to a :class:`Storage` protocol so the PostgreSQL implementation
(production) can be swapped for the in-memory one (tests / degraded mode)
without any caller changing. All methods are async.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import asyncpg

from ..domain import Symbol, Timeframe
from .models import HistoryRow, TelegramUser, UserPreferences

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Storage(Protocol):
    async def connect(self) -> None: ...
    async def close(self) -> None: ...

    async def get_or_create_user(self, user_id: int, **profile: str | None) -> TelegramUser: ...
    async def touch_user(self, user_id: int) -> None: ...
    async def set_language(self, user_id: int, language: str) -> None: ...

    async def get_preferences(self, user_id: int) -> UserPreferences: ...
    async def update_preferences(self, user_id: int, **changes: Any) -> UserPreferences: ...

    async def register_analysis_request(self, user_id: int) -> None: ...
    async def add_analysis(self, row: HistoryRow) -> int: ...
    async def set_analysis_message_id(self, row_id: int, message_id: int) -> None: ...
    async def list_history(self, user_id: int, limit: int = 10) -> list[HistoryRow]: ...
    async def get_history_row(self, user_id: int, row_id: int) -> HistoryRow | None: ...


# --------------------------------------------------------------------------
# PostgreSQL implementation
# --------------------------------------------------------------------------

class PostgresStorage:
    """Asyncpg-backed repository. Schema is applied by ``scripts/init_db.py``
    or lazily via :meth:`connect` when the tables are missing."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url
        self._pool: asyncpg.Pool | None = None

    @property
    def connected(self) -> bool:
        return self._pool is not None

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._url, min_size=1, max_size=10)
            await self._ensure_schema()

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def _ensure_schema(self) -> None:
        """Apply schema.sql (idempotent) if the core tables are absent."""
        assert self._pool is not None
        has_users = await self._pool.fetchval(
            "SELECT to_regclass('public.telegram_users') IS NOT NULL"
        )
        if has_users:
            return
        ddl = SCHEMA_PATH.read_text(encoding="utf-8")
        async with self._pool.acquire() as conn:
            await conn.execute(ddl)
        logger.info("Database schema applied")

    # -- users -------------------------------------------------------------

    async def get_or_create_user(self, user_id: int, **profile: str | None) -> TelegramUser:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            INSERT INTO telegram_users
                (user_id, username, first_name, last_name, language_code, last_active)
            VALUES ($1, $2, $3, $4, $5, now())
            ON CONFLICT (user_id) DO UPDATE SET last_active = now()
            RETURNING *
            """,
            user_id,
            profile.get("username"),
            profile.get("first_name"),
            profile.get("last_name"),
            profile.get("language_code"),
        )
        return self._user_from_row(row)

    async def touch_user(self, user_id: int) -> None:
        assert self._pool is not None
        await self._pool.execute(
            "UPDATE telegram_users SET last_active = now() WHERE user_id = $1", user_id
        )

    async def set_language(self, user_id: int, language: str) -> None:
        assert self._pool is not None
        await self._pool.execute(
            "UPDATE telegram_users SET language_code = $2 WHERE user_id = $1",
            user_id,
            language,
        )

    async def register_analysis_request(self, user_id: int) -> None:
        """Increment the daily counter, resetting it when the date changed.

        The Redis rate limiter is authoritative; this is an audit counter that
        keeps the ``telegram_users`` columns from the README schema honest.
        """
        assert self._pool is not None
        await self._pool.execute(
            """
            UPDATE telegram_users
               SET daily_requests = CASE
                       WHEN last_request_date = CURRENT_DATE THEN daily_requests + 1
                       ELSE 1
                   END,
                   last_request_date = CURRENT_DATE,
                   last_active = now()
             WHERE user_id = $1
            """,
            user_id,
        )

    @staticmethod
    def _user_from_row(row: asyncpg.Record) -> TelegramUser:
        return TelegramUser(
            user_id=row["user_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            language_code=row["language_code"] or "en",
            daily_requests=row["daily_requests"],
            last_request_date=row["last_request_date"],
            max_daily_requests=row["max_daily_requests"],
            is_premium=row["is_premium"],
            created_at=row["created_at"],
            last_active=row["last_active"],
        )

    # -- preferences -------------------------------------------------------

    async def get_preferences(self, user_id: int) -> UserPreferences:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            "SELECT * FROM user_preferences WHERE user_id = $1", user_id
        )
        if row is None:
            return UserPreferences(user_id=user_id)
        return self._prefs_from_row(row)

    async def update_preferences(self, user_id: int, **changes: Any) -> UserPreferences:
        assert self._pool is not None
        allowed = {
            "default_symbol", "default_timeframe", "show_chart", "show_indicators",
            "show_risk", "show_sentiment", "notification_enabled",
        }
        cols = [c for c in changes if c in allowed]
        if not cols:
            return await self.get_preferences(user_id)

        sets = ", ".join(f"{c} = ${i + 1}" for i, c in enumerate(cols))
        values = [changes[c] if isinstance(changes[c], (str, bool))
                  else changes[c].value if isinstance(changes[c], (Symbol, Timeframe))
                  else changes[c] for c in cols]
        query = (
            f"INSERT INTO user_preferences (user_id, {', '.join(cols)}, updated_at) "
            f"VALUES (${len(cols) + 1}, {', '.join(f'${i + 1}' for i in range(len(cols)))}, now()) "
            f"ON CONFLICT (user_id) DO UPDATE SET {sets}, updated_at = now() "
            f"RETURNING *"
        )
        row = await self._pool.fetchrow(query, *values, user_id)
        return self._prefs_from_row(row)

    @staticmethod
    def _prefs_from_row(row: asyncpg.Record) -> UserPreferences:
        return UserPreferences(
            user_id=row["user_id"],
            default_symbol=Symbol.parse(row["default_symbol"]) or Symbol.BTCUSD,
            default_timeframe=Timeframe.parse(row["default_timeframe"]) or Timeframe.H1,
            show_chart=row["show_chart"],
            show_indicators=row["show_indicators"],
            show_risk=row["show_risk"],
            show_sentiment=row["show_sentiment"],
            notification_enabled=row["notification_enabled"],
            updated_at=row["updated_at"],
        )

    # -- analysis history --------------------------------------------------

    async def add_analysis(self, row: HistoryRow) -> int:
        assert self._pool is not None
        record_id = await self._pool.fetchval(
            """
            INSERT INTO analysis_history (
                user_id, symbol, timeframe, timestamp, current_price,
                technical_score, sentiment_score, risk_score, correlation_score,
                total_score, signal, rsi, macd, ma_50, ma_200, support, resistance,
                stop_loss, take_profit, position_size_pct, atr, summary, chart_url,
                response_time_ms
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                $16, $17, $18, $19, $20, $21, $22, $23, $24
            )
            RETURNING id
            """,
            row.user_id, row.symbol, row.timeframe, row.timestamp, row.current_price,
            row.technical_score, row.sentiment_score, row.risk_score, row.correlation_score,
            row.total_score, row.signal, row.rsi, row.macd, row.ma_50, row.ma_200,
            row.support, row.resistance, row.stop_loss, row.take_profit,
            row.position_size_pct, row.atr, row.summary, row.chart_url,
            row.response_time_ms,
        )
        return int(record_id)

    async def set_analysis_message_id(self, row_id: int, message_id: int) -> None:
        assert self._pool is not None
        await self._pool.execute(
            "UPDATE analysis_history SET message_id = $2 WHERE id = $1", row_id, message_id
        )

    async def list_history(self, user_id: int, limit: int = 10) -> list[HistoryRow]:
        assert self._pool is not None
        rows = await self._pool.fetch(
            "SELECT * FROM analysis_history WHERE user_id = $1 "
            "ORDER BY timestamp DESC LIMIT $2",
            user_id,
            limit,
        )
        return [self._row_from_record(r) for r in rows]

    async def get_history_row(self, user_id: int, row_id: int) -> HistoryRow | None:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            "SELECT * FROM analysis_history WHERE id = $1 AND user_id = $2",
            row_id,
            user_id,
        )
        return self._row_from_record(row) if row else None

    @staticmethod
    def _row_from_record(row: asyncpg.Record) -> HistoryRow:
        def num(value: Any) -> float | None:
            return float(value) if value is not None else None

        return HistoryRow(
            id=int(row["id"]),
            user_id=row["user_id"],
            symbol=row["symbol"],
            timeframe=row["timeframe"],
            timestamp=row["timestamp"],
            current_price=num(row["current_price"]),
            technical_score=row["technical_score"],
            sentiment_score=row["sentiment_score"],
            risk_score=row["risk_score"],
            correlation_score=row["correlation_score"],
            total_score=row["total_score"],
            signal=row["signal"],
            rsi=num(row["rsi"]),
            macd=num(row["macd"]),
            ma_50=num(row["ma_50"]),
            ma_200=num(row["ma_200"]),
            support=num(row["support"]),
            resistance=num(row["resistance"]),
            stop_loss=num(row["stop_loss"]),
            take_profit=num(row["take_profit"]),
            position_size_pct=num(row["position_size_pct"]),
            atr=num(row["atr"]),
            summary=row["summary"],
            chart_url=row["chart_url"],
            response_time_ms=row["response_time_ms"],
            message_id=row["message_id"],
        )


# --------------------------------------------------------------------------
# In-memory implementation (tests / degraded mode)
# --------------------------------------------------------------------------

class InMemoryStorage:
    """Thread/process-local stand-in used by tests and as a graceful fallback
    when PostgreSQL is unreachable. Data does not survive restarts."""

    def __init__(self) -> None:
        self._users: dict[int, TelegramUser] = {}
        self._prefs: dict[int, UserPreferences] = {}
        self._history: list[HistoryRow] = []
        self._next_id = 1

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def get_or_create_user(self, user_id: int, **profile: str | None) -> TelegramUser:
        user = self._users.get(user_id)
        if user is None:
            language = (profile.get("language_code") or "en")
            user = TelegramUser(
                user_id=user_id,
                username=profile.get("username"),
                first_name=profile.get("first_name"),
                last_name=profile.get("last_name"),
                language_code=language,
                created_at=_utcnow(),
                last_active=_utcnow(),
            )
            self._users[user_id] = user
        else:
            user.last_active = _utcnow()
        return user

    async def touch_user(self, user_id: int) -> None:
        user = self._users.get(user_id)
        if user:
            user.last_active = _utcnow()

    async def set_language(self, user_id: int, language: str) -> None:
        user = self._users.get(user_id)
        if user:
            user.language_code = language

    async def register_analysis_request(self, user_id: int) -> None:
        user = self._users.get(user_id)
        if user:
            today = _utcnow().date()
            if user.last_request_date != today:
                user.daily_requests = 1
                user.last_request_date = today
            else:
                user.daily_requests += 1
            user.last_active = _utcnow()

    async def get_preferences(self, user_id: int) -> UserPreferences:
        prefs = self._prefs.get(user_id)
        if prefs is None:
            prefs = UserPreferences(user_id=user_id)
            self._prefs[user_id] = prefs
        return prefs

    async def update_preferences(self, user_id: int, **changes: Any) -> UserPreferences:
        prefs = await self.get_preferences(user_id)
        mapping = {
            "default_symbol": lambda v: Symbol.parse(v) or Symbol.BTCUSD if isinstance(v, str) else v,
            "default_timeframe": lambda v: Timeframe.parse(v) or Timeframe.H1 if isinstance(v, str) else v,
        }
        for key, value in changes.items():
            if key in mapping:
                value = mapping[key](value)
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        prefs.updated_at = _utcnow()
        return prefs

    async def add_analysis(self, row: HistoryRow) -> int:
        stored = replace(row, id=self._next_id)
        self._history.append(stored)
        self._next_id += 1
        return int(stored.id)  # type: ignore[arg-type]

    async def set_analysis_message_id(self, row_id: int, message_id: int) -> None:
        for row in self._history:
            if row.id == row_id:
                row.message_id = message_id
                return

    async def list_history(self, user_id: int, limit: int = 10) -> list[HistoryRow]:
        rows = [r for r in self._history if r.user_id == user_id]
        rows.sort(key=lambda r: r.timestamp, reverse=True)
        return rows[:limit]

    async def get_history_row(self, user_id: int, row_id: int) -> HistoryRow | None:
        for row in self._history:
            if row.id == row_id and row.user_id == user_id:
                return row
        return None
