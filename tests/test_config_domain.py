"""Tests for settings and domain enum helpers."""

from __future__ import annotations

from tradingbot.config import Settings
from tradingbot.domain import Symbol, Timeframe


def test_symbol_parse_variants():
    assert Symbol.parse("btcusd") == Symbol.BTCUSD
    assert Symbol.parse("BTC/USD") == Symbol.BTCUSD
    assert Symbol.parse("BTCUSDT") == Symbol.BTCUSD  # exchange alias
    assert Symbol.parse("xauusd") == Symbol.XAUUSD
    assert Symbol.parse("ETHUSD") is None


def test_symbol_counterparts():
    assert Symbol.BTCUSD.counterpart() == Symbol.XAUUSD
    assert Symbol.XAUUSD.counterpart() == Symbol.BTCUSD


def test_timeframe_parse_and_minutes():
    assert Timeframe.parse("4H") == Timeframe.H4
    assert Timeframe.parse("weekly") is None
    assert Timeframe.H1.minutes() == 60
    assert Timeframe.D1.minutes() == 1440
    assert Timeframe.W1.minutes() == 10080


def test_settings_defaults():
    settings = Settings()
    assert settings.default_symbol == Symbol.BTCUSD
    assert settings.default_timeframe == Timeframe.H1
    assert settings.max_daily_requests == 10
    assert settings.chart_enabled is True
    assert settings.demo_fallback is True
    assert settings.use_demo_data is False


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
    assert settings.default_symbol == Symbol.BTCUSD  # falls back safely
    assert settings.max_daily_requests == 10
    assert settings.log_level == "DEBUG"
