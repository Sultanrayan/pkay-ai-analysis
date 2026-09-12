"""Persistence layer.

The bot talks to a :class:`Storage` protocol so the PostgreSQL implementation
(production) can be swapped for the in-memory one (tests / degraded mode)
without any caller changing. All methods are async.
"""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

import asyncpg

from ..domain import Symbol, Timeframe
from .models import (
    ApiKey,
    ApiUsageSummary,
    ApiUser,
    ApiUserSettings,
    HistoryRow,
    TelegramUser,
    UserPreferences,
)

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

#: Idempotent column additions applied to pre-V3 databases on connect. Fresh
#: installs get them from schema.sql; existing ones catch up here.
_COLUMN_MIGRATIONS: tuple[str, ...] = (
    "ALTER TABLE analysis_history ADD COLUMN IF NOT EXISTS volume_score INTEGER",
    "ALTER TABLE analysis_history ADD COLUMN IF NOT EXISTS volatility_score INTEGER",
    "ALTER TABLE analysis_history ADD COLUMN IF NOT EXISTS pattern_score INTEGER",
    "ALTER TABLE analysis_history ADD COLUMN IF NOT EXISTS onchain_score INTEGER",
    "ALTER TABLE analysis_history ADD COLUMN IF NOT EXISTS macro_score INTEGER",
    "ALTER TABLE analysis_history ADD COLUMN IF NOT EXISTS sniper_score INTEGER",
    "ALTER TABLE analysis_history ADD COLUMN IF NOT EXISTS confidence NUMERIC(6, 2)",
    "ALTER TABLE analysis_history ADD COLUMN IF NOT EXISTS llm_enhanced BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE analysis_history ADD COLUMN IF NOT EXISTS agent_contributions JSONB",
    "ALTER TABLE api_users ADD COLUMN IF NOT EXISTS password_hash TEXT",
)


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

    # -- public API (v3) ---------------------------------------------------
    async def get_or_create_api_user(self, google_sub: str, **profile: str | None) -> ApiUser: ...
    async def get_api_user(self, user_id: int) -> ApiUser | None: ...

    async def create_api_key(
        self,
        *,
        key_hash: str,
        key_prefix: str,
        name: str = "Untitled key",
        environment: str = "live",
        scopes: tuple[str, ...] = (),
        user_id: int | None = None,
    ) -> ApiKey: ...
    async def get_api_key_by_hash(self, key_hash: str) -> ApiKey | None: ...
    async def list_api_keys(self, user_id: int | None = None) -> list[ApiKey]: ...
    async def revoke_api_key(self, key_id: int) -> None: ...
    async def touch_api_key(self, key_id: int) -> None: ...

    async def record_api_usage(
        self,
        *,
        key_id: int | None,
        endpoint: str,
        status_code: int,
        method: str = "POST",
        symbol: str | None = None,
        timeframe: str | None = None,
        model: str | None = None,
        latency_ms: int | None = None,
    ) -> None: ...
    async def api_usage_summary(
        self, key_id: int | None = None, days: int = 30
    ) -> ApiUsageSummary: ...
    async def delete_api_key(self, key_id: int, user_id: int) -> None: ...
    async def user_usage_summary(
        self, user_id: int, days: int = 30
    ) -> ApiUsageSummary: ...
    async def api_usage_series(
        self, user_id: int, days: int = 14
    ) -> list[dict[str, Any]]: ...
    async def api_usage_breakdown(
        self, user_id: int, field: str, limit: int = 5
    ) -> list[dict[str, Any]]: ...
    async def recent_api_usage(
        self, user_id: int, limit: int = 8
    ) -> list[dict[str, Any]]: ...
    async def get_user_settings(self, user_id: int) -> ApiUserSettings: ...
    async def update_user_settings(
        self, user_id: int, **changes: Any
    ) -> ApiUserSettings: ...
    async def set_api_user_password(self, user_id: int, password_hash: str) -> None: ...
    async def get_api_user_password_hash(self, user_id: int) -> str | None: ...


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
        """Apply schema.sql (idempotent) and additive column migrations.

        The DDL uses ``CREATE TABLE IF NOT EXISTS`` so it is safe to run on
        every connect; this also creates newly added tables (API accounts,
        keys, usage) on databases that already had the older schema.
        """
        assert self._pool is not None
        ddl = SCHEMA_PATH.read_text(encoding="utf-8")
        async with self._pool.acquire() as conn:
            await conn.execute(ddl)
            for statement in _COLUMN_MIGRATIONS:
                await conn.execute(statement)
        logger.info("Database schema up to date")

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
            default_symbol=Symbol.parse(row["default_symbol"]) or Symbol.BTCUSDT,
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
                technical_score, volume_score, volatility_score, pattern_score,
                sentiment_score, onchain_score, macro_score, risk_score,
                correlation_score, sniper_score, total_score, confidence, signal,
                rsi, macd, ma_50, ma_200, support, resistance,
                stop_loss, take_profit, position_size_pct, atr, summary, chart_url,
                response_time_ms, llm_enhanced, agent_contributions
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27,
                $28, $29, $30, $31, $32, $33
            )
            RETURNING id
            """,
            row.user_id, row.symbol, row.timeframe, row.timestamp, row.current_price,
            row.technical_score, row.volume_score, row.volatility_score, row.pattern_score,
            row.sentiment_score, row.onchain_score, row.macro_score, row.risk_score,
            row.correlation_score, row.sniper_score, row.total_score, row.confidence,
            row.signal, row.rsi, row.macd, row.ma_50, row.ma_200, row.support,
            row.resistance, row.stop_loss, row.take_profit, row.position_size_pct,
            row.atr, row.summary, row.chart_url, row.response_time_ms,
            row.llm_enhanced, row.agent_contributions,
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
            volume_score=row["volume_score"],
            volatility_score=row["volatility_score"],
            pattern_score=row["pattern_score"],
            sentiment_score=row["sentiment_score"],
            onchain_score=row["onchain_score"],
            macro_score=row["macro_score"],
            risk_score=row["risk_score"],
            correlation_score=row["correlation_score"],
            sniper_score=row["sniper_score"],
            total_score=row["total_score"],
            confidence=num(row["confidence"]),
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
            llm_enhanced=row.get("llm_enhanced", False),
            agent_contributions=row.get("agent_contributions"),
        )

    # -- public API (v3) ---------------------------------------------------

    async def get_or_create_api_user(
        self, google_sub: str, **profile: str | None
    ) -> ApiUser:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            INSERT INTO api_users (google_sub, email, name, picture, last_login)
            VALUES ($1, $2, $3, $4, now())
            ON CONFLICT (google_sub) DO UPDATE SET
                email = COALESCE(EXCLUDED.email, api_users.email),
                name = COALESCE(EXCLUDED.name, api_users.name),
                picture = COALESCE(EXCLUDED.picture, api_users.picture),
                last_login = now()
            RETURNING *
            """,
            google_sub,
            profile.get("email"),
            profile.get("name"),
            profile.get("picture"),
        )
        return self._api_user_from_row(row)

    async def get_api_user(self, user_id: int) -> ApiUser | None:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            "SELECT * FROM api_users WHERE id = $1", user_id
        )
        return self._api_user_from_row(row) if row else None

    @staticmethod
    def _api_user_from_row(row: asyncpg.Record) -> ApiUser:
        return ApiUser(
            id=int(row["id"]),
            google_sub=row["google_sub"],
            email=row["email"],
            name=row["name"],
            picture=row["picture"],
            plan=row["plan"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )

    async def create_api_key(
        self,
        *,
        key_hash: str,
        key_prefix: str,
        name: str = "Untitled key",
        environment: str = "live",
        scopes: tuple[str, ...] = (),
        user_id: int | None = None,
    ) -> ApiKey:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            INSERT INTO api_keys (user_id, name, key_prefix, key_hash, environment, scopes)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            user_id,
            name,
            key_prefix,
            key_hash,
            environment,
            list(scopes),
        )
        return self._api_key_from_row(row)

    async def get_api_key_by_hash(self, key_hash: str) -> ApiKey | None:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            "SELECT * FROM api_keys WHERE key_hash = $1", key_hash
        )
        return self._api_key_from_row(row) if row else None

    async def list_api_keys(self, user_id: int | None = None) -> list[ApiKey]:
        assert self._pool is not None
        rows = await self._pool.fetch(
            """
            SELECT * FROM api_keys
             WHERE ($1::bigint IS NULL OR user_id = $1)
             ORDER BY created_at DESC
            """,
            user_id,
        )
        return [self._api_key_from_row(row) for row in rows]

    async def revoke_api_key(self, key_id: int) -> None:
        assert self._pool is not None
        await self._pool.execute(
            "UPDATE api_keys SET revoked_at = now() "
            "WHERE id = $1 AND revoked_at IS NULL",
            key_id,
        )

    async def touch_api_key(self, key_id: int) -> None:
        assert self._pool is not None
        await self._pool.execute(
            "UPDATE api_keys SET last_used_at = now(), "
            "request_count = request_count + 1 WHERE id = $1",
            key_id,
        )

    @staticmethod
    def _api_key_from_row(row: asyncpg.Record) -> ApiKey:
        return ApiKey(
            id=int(row["id"]),
            user_id=row["user_id"],
            name=row["name"],
            key_prefix=row["key_prefix"],
            key_hash=row["key_hash"],
            environment=row["environment"],
            scopes=tuple(row["scopes"] or ()),
            request_count=row["request_count"],
            created_at=row["created_at"],
            last_used_at=row["last_used_at"],
            revoked_at=row["revoked_at"],
        )

    async def record_api_usage(
        self,
        *,
        key_id: int | None,
        endpoint: str,
        status_code: int,
        method: str = "POST",
        symbol: str | None = None,
        timeframe: str | None = None,
        model: str | None = None,
        latency_ms: int | None = None,
    ) -> None:
        assert self._pool is not None
        await self._pool.execute(
            """
            INSERT INTO api_usage
                (key_id, endpoint, method, status_code, symbol, timeframe, model, latency_ms)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            key_id,
            endpoint,
            method,
            status_code,
            symbol,
            timeframe,
            model,
            latency_ms,
        )

    async def api_usage_summary(
        self, key_id: int | None = None, days: int = 30
    ) -> ApiUsageSummary:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) AS today,
                   COUNT(*) FILTER (WHERE status_code >= 400) AS errors
              FROM api_usage
             WHERE created_at >= now() - make_interval(days => $1)
               AND ($2::bigint IS NULL OR key_id = $2)
            """,
            days,
            key_id,
        )
        total = int(row["total"] or 0)
        errors = int(row["errors"] or 0)
        success = 100.0 if total == 0 else round((total - errors) / total * 100, 1)
        return ApiUsageSummary(
            total=total,
            today=int(row["today"] or 0),
            errors=errors,
            success_rate=success,
        )

    async def delete_api_key(self, key_id: int, user_id: int) -> None:
        assert self._pool is not None
        await self._pool.execute(
            "DELETE FROM api_keys WHERE id = $1 AND user_id = $2", key_id, user_id
        )

    async def user_usage_summary(
        self, user_id: int, days: int = 30
    ) -> ApiUsageSummary:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE u.created_at >= CURRENT_DATE) AS today,
                   COUNT(*) FILTER (WHERE u.status_code >= 400) AS errors
              FROM api_usage u
              JOIN api_keys k ON k.id = u.key_id
             WHERE k.user_id = $1
               AND u.created_at >= now() - make_interval(days => $2)
            """,
            user_id,
            days,
        )
        total = int(row["total"] or 0)
        errors = int(row["errors"] or 0)
        success = 100.0 if total == 0 else round((total - errors) / total * 100, 1)
        return ApiUsageSummary(
            total=total,
            today=int(row["today"] or 0),
            errors=errors,
            success_rate=success,
        )

    async def api_usage_series(
        self, user_id: int, days: int = 14
    ) -> list[dict[str, Any]]:
        assert self._pool is not None
        rows = await self._pool.fetch(
            """
            SELECT to_char(u.created_at, 'MM-DD') AS day,
                   COUNT(*) AS requests,
                   COUNT(*) FILTER (WHERE u.status_code >= 400) AS errors,
                   COUNT(*) FILTER (WHERE u.endpoint = '/api/v3/analyze') AS analyses,
                   COUNT(*) FILTER (WHERE u.endpoint = '/api/v3/agents') AS agents
              FROM api_usage u
              JOIN api_keys k ON k.id = u.key_id
             WHERE k.user_id = $1
               AND u.created_at >= now() - make_interval(days => $2)
             GROUP BY day
             ORDER BY day
            """,
            user_id,
            days,
        )
        by_day = {row["day"]: row for row in rows}
        today = _utcnow().date()
        series: list[dict[str, Any]] = []
        for offset in range(days - 1, -1, -1):
            day = (today - timedelta(days=offset)).strftime("%m-%d")
            row = by_day.get(day)
            series.append(
                {
                    "date": day,
                    "requests": int(row["requests"]) if row else 0,
                    "errors": int(row["errors"]) if row else 0,
                    "analyses": int(row["analyses"]) if row else 0,
                    "agents": int(row["agents"]) if row else 0,
                }
            )
        return series

    async def api_usage_breakdown(
        self, user_id: int, field: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        assert self._pool is not None
        columns = {
            "endpoint": "u.endpoint",
            "model": "u.model",
            "symbol": "u.symbol",
            "timeframe": "u.timeframe",
        }
        column = columns.get(field)
        if column is None:
            raise ValueError(f"Unsupported breakdown field: {field}")
        rows = await self._pool.fetch(
            f"""
            SELECT COALESCE({column}, 'unknown') AS label, COUNT(*) AS count
              FROM api_usage u
              JOIN api_keys k ON k.id = u.key_id
             WHERE k.user_id = $1
             GROUP BY label
             ORDER BY count DESC
             LIMIT $2
            """,
            user_id,
            limit,
        )
        return [{"label": row["label"], "count": int(row["count"])} for row in rows]

    async def recent_api_usage(
        self, user_id: int, limit: int = 8
    ) -> list[dict[str, Any]]:
        assert self._pool is not None
        rows = await self._pool.fetch(
            """
            SELECT u.endpoint, u.method, u.status_code, u.symbol, u.timeframe,
                   u.model, u.latency_ms, u.created_at
              FROM api_usage u
              JOIN api_keys k ON k.id = u.key_id
             WHERE k.user_id = $1
             ORDER BY u.created_at DESC
             LIMIT $2
            """,
            user_id,
            limit,
        )
        return [
            {
                "endpoint": row["endpoint"],
                "method": row["method"],
                "status_code": row["status_code"],
                "symbol": row["symbol"],
                "timeframe": row["timeframe"],
                "model": row["model"],
                "latency_ms": row["latency_ms"],
                "created_at": row["created_at"].isoformat()
                if row["created_at"]
                else None,
            }
            for row in rows
        ]

    async def get_user_settings(self, user_id: int) -> ApiUserSettings:
        assert self._pool is not None
        row = await self._pool.fetchrow(
            "SELECT * FROM api_user_settings WHERE user_id = $1", user_id
        )
        if row is None:
            return ApiUserSettings(user_id=user_id)
        return self._settings_from_row(row)

    async def update_user_settings(
        self, user_id: int, **changes: Any
    ) -> ApiUserSettings:
        assert self._pool is not None
        allowed = {
            "language",
            "currency",
            "timezone",
            "theme",
            "density",
            "default_model",
            "default_symbol",
            "default_timeframe",
            "notifications",
        }
        cols = [column for column in changes if column in allowed]
        if not cols:
            return await self.get_user_settings(user_id)

        await self._pool.execute(
            "INSERT INTO api_user_settings (user_id) VALUES ($1) "
            "ON CONFLICT (user_id) DO NOTHING",
            user_id,
        )
        values = [
            json.dumps(changes[column])
            if column == "notifications"
            else changes[column]
            for column in cols
        ]
        sets = ", ".join(f"{column} = ${index + 1}" for index, column in enumerate(cols))
        row = await self._pool.fetchrow(
            f"UPDATE api_user_settings SET {sets}, updated_at = now() "
            f"WHERE user_id = ${len(cols) + 1} RETURNING *",
            *values,
            user_id,
        )
        return self._settings_from_row(row)

    @staticmethod
    def _settings_from_row(row: asyncpg.Record) -> ApiUserSettings:
        notifications = row["notifications"]
        if isinstance(notifications, str):
            try:
                notifications = json.loads(notifications)
            except (TypeError, ValueError):
                notifications = {}
        return ApiUserSettings(
            user_id=row["user_id"],
            language=row["language"],
            currency=row["currency"],
            timezone=row["timezone"],
            theme=row["theme"],
            density=row["density"],
            default_model=row["default_model"],
            default_symbol=row["default_symbol"],
            default_timeframe=row["default_timeframe"],
            notifications=notifications or {},
            updated_at=row["updated_at"],
        )

    async def set_api_user_password(self, user_id: int, password_hash: str) -> None:
        assert self._pool is not None
        await self._pool.execute(
            "UPDATE api_users SET password_hash = $2 WHERE id = $1",
            user_id,
            password_hash,
        )

    async def get_api_user_password_hash(self, user_id: int) -> str | None:
        assert self._pool is not None
        return await self._pool.fetchval(
            "SELECT password_hash FROM api_users WHERE id = $1", user_id
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
        self._api_users: dict[int, ApiUser] = {}
        self._api_keys: dict[int, ApiKey] = {}
        self._api_usage: list[dict[str, Any]] = []
        self._api_settings: dict[int, ApiUserSettings] = {}
        self._api_passwords: dict[int, str] = {}
        self._next_api_user_id = 1
        self._next_api_key_id = 1

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
            "default_symbol": lambda v: Symbol.parse(v) or Symbol.BTCUSDT if isinstance(v, str) else v,
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

    # -- public API (v3) ---------------------------------------------------

    async def get_or_create_api_user(
        self, google_sub: str, **profile: str | None
    ) -> ApiUser:
        for user in self._api_users.values():
            if user.google_sub == google_sub:
                user.email = profile.get("email") or user.email
                user.name = profile.get("name") or user.name
                user.picture = profile.get("picture") or user.picture
                user.last_login = _utcnow()
                return user
        user = ApiUser(
            id=self._next_api_user_id,
            google_sub=google_sub,
            email=profile.get("email"),
            name=profile.get("name"),
            picture=profile.get("picture"),
            created_at=_utcnow(),
            last_login=_utcnow(),
        )
        self._api_users[user.id] = user  # type: ignore[index]
        self._next_api_user_id += 1
        return user

    async def get_api_user(self, user_id: int) -> ApiUser | None:
        return self._api_users.get(user_id)

    async def create_api_key(
        self,
        *,
        key_hash: str,
        key_prefix: str,
        name: str = "Untitled key",
        environment: str = "live",
        scopes: tuple[str, ...] = (),
        user_id: int | None = None,
    ) -> ApiKey:
        key = ApiKey(
            id=self._next_api_key_id,
            user_id=user_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            environment=environment,
            scopes=tuple(scopes),
            created_at=_utcnow(),
        )
        self._api_keys[key.id] = key  # type: ignore[index]
        self._next_api_key_id += 1
        return key

    async def get_api_key_by_hash(self, key_hash: str) -> ApiKey | None:
        for key in self._api_keys.values():
            if key.key_hash == key_hash:
                return key
        return None

    async def list_api_keys(self, user_id: int | None = None) -> list[ApiKey]:
        keys = [
            key
            for key in self._api_keys.values()
            if user_id is None or key.user_id == user_id
        ]
        keys.sort(key=lambda key: key.created_at or _utcnow(), reverse=True)
        return keys

    async def revoke_api_key(self, key_id: int) -> None:
        key = self._api_keys.get(key_id)
        if key is not None and key.revoked_at is None:
            key.revoked_at = _utcnow()

    async def touch_api_key(self, key_id: int) -> None:
        key = self._api_keys.get(key_id)
        if key is not None:
            key.last_used_at = _utcnow()
            key.request_count += 1

    async def record_api_usage(
        self,
        *,
        key_id: int | None,
        endpoint: str,
        status_code: int,
        method: str = "POST",
        symbol: str | None = None,
        timeframe: str | None = None,
        model: str | None = None,
        latency_ms: int | None = None,
    ) -> None:
        self._api_usage.append(
            {
                "key_id": key_id,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "symbol": symbol,
                "timeframe": timeframe,
                "model": model,
                "latency_ms": latency_ms,
                "created_at": _utcnow(),
            }
        )

    async def api_usage_summary(
        self, key_id: int | None = None, days: int = 30
    ) -> ApiUsageSummary:
        cutoff = _utcnow() - timedelta(days=days)
        rows = [
            row
            for row in self._api_usage
            if row["created_at"] >= cutoff
            and (key_id is None or row["key_id"] == key_id)
        ]
        total = len(rows)
        today = _utcnow().date()
        errors = sum(1 for row in rows if row["status_code"] >= 400)
        success = 100.0 if total == 0 else round((total - errors) / total * 100, 1)
        return ApiUsageSummary(
            total=total,
            today=sum(1 for row in rows if row["created_at"].date() == today),
            errors=errors,
            success_rate=success,
        )

    async def delete_api_key(self, key_id: int, user_id: int) -> None:
        key = self._api_keys.get(key_id)
        if key is not None and key.user_id == user_id:
            self._api_keys.pop(key_id, None)

    def _user_usage_rows(self, user_id: int, days: int) -> list[dict[str, Any]]:
        cutoff = _utcnow() - timedelta(days=days)
        key_ids = {
            key.id
            for key in self._api_keys.values()
            if key.user_id == user_id
        }
        return [
            row
            for row in self._api_usage
            if row["key_id"] in key_ids and row["created_at"] >= cutoff
        ]

    async def user_usage_summary(
        self, user_id: int, days: int = 30
    ) -> ApiUsageSummary:
        rows = self._user_usage_rows(user_id, days)
        total = len(rows)
        errors = sum(1 for row in rows if row["status_code"] >= 400)
        today = _utcnow().date()
        success = 100.0 if total == 0 else round((total - errors) / total * 100, 1)
        return ApiUsageSummary(
            total=total,
            today=sum(1 for row in rows if row["created_at"].date() == today),
            errors=errors,
            success_rate=success,
        )

    async def api_usage_series(
        self, user_id: int, days: int = 14
    ) -> list[dict[str, Any]]:
        rows = self._user_usage_rows(user_id, days)
        today = _utcnow().date()
        counts: dict[Any, dict[str, int]] = {}
        for row in rows:
            day = row["created_at"].date()
            bucket = counts.setdefault(
                day, {"requests": 0, "errors": 0, "analyses": 0, "agents": 0}
            )
            bucket["requests"] += 1
            if row["status_code"] >= 400:
                bucket["errors"] += 1
            if row["endpoint"] == "/api/v3/analyze":
                bucket["analyses"] += 1
            if row["endpoint"] == "/api/v3/agents":
                bucket["agents"] += 1

        series: list[dict[str, Any]] = []
        for offset in range(days - 1, -1, -1):
            day = today - timedelta(days=offset)
            bucket = counts.get(
                day, {"requests": 0, "errors": 0, "analyses": 0, "agents": 0}
            )
            series.append({"date": day.strftime("%m-%d"), **bucket})
        return series

    async def api_usage_breakdown(
        self, user_id: int, field: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        if field not in ("endpoint", "model", "symbol", "timeframe"):
            raise ValueError(f"Unsupported breakdown field: {field}")
        rows = self._user_usage_rows(user_id, 3650)
        counts: dict[str, int] = {}
        for row in rows:
            label = row.get(field) or "unknown"
            counts[label] = counts.get(label, 0) + 1
        ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        return [
            {"label": label, "count": count} for label, count in ordered[:limit]
        ]

    async def recent_api_usage(
        self, user_id: int, limit: int = 8
    ) -> list[dict[str, Any]]:
        rows = self._user_usage_rows(user_id, 3650)
        rows.sort(key=lambda row: row["created_at"], reverse=True)
        return [
            {
                "endpoint": row["endpoint"],
                "method": row["method"],
                "status_code": row["status_code"],
                "symbol": row["symbol"],
                "timeframe": row["timeframe"],
                "model": row["model"],
                "latency_ms": row["latency_ms"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows[:limit]
        ]

    async def get_user_settings(self, user_id: int) -> ApiUserSettings:
        settings = self._api_settings.get(user_id)
        if settings is None:
            settings = ApiUserSettings(user_id=user_id)
            self._api_settings[user_id] = settings
        return settings

    async def update_user_settings(
        self, user_id: int, **changes: Any
    ) -> ApiUserSettings:
        settings = await self.get_user_settings(user_id)
        for key, value in changes.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        settings.updated_at = _utcnow()
        return settings

    async def set_api_user_password(self, user_id: int, password_hash: str) -> None:
        self._api_passwords[user_id] = password_hash

    async def get_api_user_password_hash(self, user_id: int) -> str | None:
        return self._api_passwords.get(user_id)
