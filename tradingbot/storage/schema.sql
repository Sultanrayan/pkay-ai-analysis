-- Trading Analysis Bot schema (PostgreSQL).
-- Mirrors the database schema documented in README.md. Applied by
-- `scripts/init_db.py` and idempotent (CREATE IF NOT EXISTS) so it can be
-- re-run safely.

CREATE TABLE IF NOT EXISTS telegram_users (
    user_id           BIGINT PRIMARY KEY,
    username          TEXT,
    first_name        TEXT,
    last_name         TEXT,
    language_code     TEXT        DEFAULT 'en',
    daily_requests    INTEGER     NOT NULL DEFAULT 0,
    last_request_date DATE,
    max_daily_requests INTEGER    NOT NULL DEFAULT 10,
    is_premium        BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_active       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analysis_history (
    id                 BIGSERIAL PRIMARY KEY,
    user_id            BIGINT      NOT NULL REFERENCES telegram_users (user_id) ON DELETE CASCADE,
    symbol             TEXT        NOT NULL,
    timeframe          TEXT        NOT NULL,
    timestamp          TIMESTAMPTZ NOT NULL DEFAULT now(),
    current_price      NUMERIC(20, 6),
    technical_score    INTEGER,
    sentiment_score    INTEGER,
    risk_score         INTEGER,
    correlation_score  INTEGER,
    total_score        INTEGER,
    signal             TEXT,
    rsi                NUMERIC(10, 4),
    macd               NUMERIC(20, 8),
    ma_50              NUMERIC(20, 6),
    ma_200             NUMERIC(20, 6),
    support            NUMERIC(20, 6),
    resistance         NUMERIC(20, 6),
    stop_loss          NUMERIC(20, 6),
    take_profit        NUMERIC(20, 6),
    position_size_pct  NUMERIC(10, 4),
    atr                NUMERIC(20, 8),
    summary            TEXT,
    chart_url          TEXT,
    response_time_ms   INTEGER,
    message_id         BIGINT
);

CREATE INDEX IF NOT EXISTS idx_analysis_history_user_time
    ON analysis_history (user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id              BIGINT PRIMARY KEY REFERENCES telegram_users (user_id) ON DELETE CASCADE,
    default_symbol       TEXT        NOT NULL DEFAULT 'BTCUSD',
    default_timeframe    TEXT        NOT NULL DEFAULT '1h',
    show_chart           BOOLEAN     NOT NULL DEFAULT TRUE,
    show_indicators      BOOLEAN     NOT NULL DEFAULT TRUE,
    show_risk            BOOLEAN     NOT NULL DEFAULT TRUE,
    show_sentiment       BOOLEAN     NOT NULL DEFAULT TRUE,
    notification_enabled TEXT        NOT NULL DEFAULT 'daily',
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
