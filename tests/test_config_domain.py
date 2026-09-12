"""Tests for settings and domain enum helpers."""

from __future__ import annotations

from tradingbot.config import Settings
from tradingbot.domain import Symbol, Timeframe


def test_symbol_parse_variants():
    assert Symbol.parse("btcusd") == Symbol.BTCUSDT  # legacy alias
    assert Symbol.parse("BTC/USD") == Symbol.BTCUSDT
    assert Symbol.parse("BTCUSDT") == Symbol.BTCUSDT
    assert Symbol.parse("BTC-USD") == Symbol.BTCUSDT
    assert Symbol.parse("ethusdt") == Symbol.ETHUSDT
    assert Symbol.parse("sol-usdt") == Symbol.SOLUSDT
    assert Symbol.parse("xauusd") == Symbol.XAUUSD
    assert Symbol.parse("ETHUSD") is None  # no such market


def test_symbol_correlation_peers():
    assert Symbol.BTCUSDT.correlation_peer() == Symbol.XAUUSD
    assert Symbol.XAUUSD.correlation_peer() == Symbol.BTCUSDT
    assert Symbol.ETHUSDT.correlation_peer() == Symbol.SOLUSDT
    assert Symbol.SOLUSDT.correlation_peer() == Symbol.ETHUSDT


def test_timeframe_parse_and_minutes():
    assert Timeframe.parse("4H") == Timeframe.H4
    assert Timeframe.parse("weekly") is None
    assert Timeframe.H1.minutes() == 60
    assert Timeframe.D1.minutes() == 1440
    assert Timeframe.W1.minutes() == 10080


def test_timeframe_intraday_and_aliases():
    assert Timeframe.parse("1m") == Timeframe.M1
    assert Timeframe.parse("5min") == Timeframe.M5
    assert Timeframe.parse("15min") == Timeframe.M15
    assert Timeframe.parse("1week") == Timeframe.W1
    assert Timeframe.parse("60m") == Timeframe.H1
    assert Timeframe.M1.minutes() == 1
    assert Timeframe.M5.minutes() == 5
    assert Timeframe.M15.minutes() == 15
    assert [tf.value for tf in Timeframe] == [
        "1m",
        "5m",
        "15m",
        "1h",
        "4h",
        "1d",
        "1w",
    ]


def test_settings_defaults():
    settings = Settings()
    assert settings.default_symbol == Symbol.BTCUSDT
    assert settings.default_timeframe == Timeframe.H1
    assert settings.max_daily_requests == 10
    assert settings.chart_enabled is True
    assert settings.demo_fallback is True
    assert settings.use_demo_data is False
    assert settings.deepseek_model == "deepseek-v4-flash"
    assert settings.deepseek_api_key == ""
    assert settings.sniper_enabled is True
    assert settings.sniper_min_liquidity == 500_000.0


def test_settings_from_env_respects_overrides(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEFAULT_SYMBOL=xauusd\nDEFAULT_TIMEFRAME=1w\nMAX_DAILY_REQUESTS=3\nUSE_DEMO_DATA=true\n"
        "TELEGRAM_BOT_TOKEN=abc123\nCHART_PATH=./tmp_charts\n",
        encoding="utf-8",
    )
    settings = Settings.from_env(str(env_file), override=True)
    assert settings.default_symbol == Symbol.XAUUSD
    assert settings.default_timeframe == Timeframe.W1
    assert settings.max_daily_requests == 3
    assert settings.use_demo_data is True
    assert settings.telegram_bot_token == "abc123"
    assert settings.chart_path.name == "tmp_charts"  # path normalised


def test_settings_from_env_ignores_garbage_values(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEFAULT_SYMBOL=not_a_symbol\nMAX_DAILY_REQUESTS=banana\nLOG_LEVEL=DEBUG\n",
        encoding="utf-8",
    )
    settings = Settings.from_env(str(env_file), override=True)
    assert settings.default_symbol == Symbol.BTCUSDT  # falls back safely
    assert settings.max_daily_requests == 10
    assert settings.log_level == "DEBUG"
