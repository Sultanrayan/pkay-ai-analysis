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
    volume_score       INTEGER,
    volatility_score   INTEGER,
    pattern_score      INTEGER,
    sentiment_score    INTEGER,
    onchain_score      INTEGER,
    macro_score        INTEGER,
    risk_score         INTEGER,
    correlation_score  INTEGER,
    sniper_score       INTEGER,
    total_score        INTEGER,
    confidence         NUMERIC(6, 2),
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
    message_id         BIGINT,
    llm_enhanced       BOOLEAN     NOT NULL DEFAULT FALSE,
    agent_contributions JSONB
);

CREATE INDEX IF NOT EXISTS idx_analysis_history_user_time
    ON analysis_history (user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id              BIGINT PRIMARY KEY REFERENCES telegram_users (user_id) ON DELETE CASCADE,
    default_symbol       TEXT        NOT NULL DEFAULT 'BTCUSDT',
    default_timeframe    TEXT        NOT NULL DEFAULT '1h',
    show_chart           BOOLEAN     NOT NULL DEFAULT TRUE,
    show_indicators      BOOLEAN     NOT NULL DEFAULT TRUE,
    show_risk            BOOLEAN     NOT NULL DEFAULT TRUE,
    show_sentiment       BOOLEAN     NOT NULL DEFAULT TRUE,
    notification_enabled TEXT        NOT NULL DEFAULT 'daily',
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Public API (v3): accounts, hashed keys and request usage.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS api_users (
    id          BIGSERIAL PRIMARY KEY,
    google_sub  TEXT UNIQUE,                 -- Google subject id
    email       TEXT,
    name        TEXT,
    picture     TEXT,
    password_hash TEXT,                      -- optional password (PBKDF2)
    plan        TEXT        NOT NULL DEFAULT 'free',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS api_user_settings (
    user_id           BIGINT PRIMARY KEY REFERENCES api_users (id) ON DELETE CASCADE,
    language          TEXT        NOT NULL DEFAULT 'en',
    currency          TEXT        NOT NULL DEFAULT 'usd',
    timezone          TEXT        NOT NULL DEFAULT 'utc',
    theme             TEXT        NOT NULL DEFAULT 'dark',
    density           TEXT        NOT NULL DEFAULT 'comfortable',
    default_model     TEXT        NOT NULL DEFAULT 'deepseek-v4-flash',
    default_symbol    TEXT        NOT NULL DEFAULT 'BTCUSDT',
    default_timeframe TEXT        NOT NULL DEFAULT '1h',
    notifications     JSONB       NOT NULL DEFAULT '{}'::jsonb,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS api_keys (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES api_users (id) ON DELETE CASCADE,
    name          TEXT        NOT NULL DEFAULT 'Untitled key',
    key_prefix    TEXT        NOT NULL,      -- safe display prefix (e.g. pk_live_ab12)
    key_hash      TEXT        NOT NULL UNIQUE, -- sha256 of the raw key
    environment   TEXT        NOT NULL DEFAULT 'live',
    scopes        TEXT[]      NOT NULL DEFAULT '{}',
    request_count BIGINT      NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_used_at  TIMESTAMPTZ,
    revoked_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys (key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS api_usage (
    id          BIGSERIAL PRIMARY KEY,
    key_id      BIGINT REFERENCES api_keys (id) ON DELETE SET NULL,
    endpoint    TEXT        NOT NULL,
    method      TEXT        NOT NULL DEFAULT 'POST',
    status_code INTEGER     NOT NULL,
    symbol      TEXT,
    timeframe   TEXT,
    model       TEXT,
    latency_ms  INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_api_usage_key_time ON api_usage (key_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_time ON api_usage (created_at DESC);
