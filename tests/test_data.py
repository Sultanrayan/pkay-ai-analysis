"""Tests for provider parsing, the demo generator and the data manager."""

from __future__ import annotations

import pytest

from tradingbot.config import Settings
from tradingbot.data.manager import MarketDataManager
from tradingbot.data.providers import (
    DemoProvider,
    ProviderError,
    candle_to_dict,
    candles_from_dicts,
    parse_binance_klines,
    parse_yahoo_chart,
)
from tradingbot.domain import Symbol, Timeframe

# --------------------------------------------------------------------------
# Parsers (pure, offline)
# --------------------------------------------------------------------------

def test_parse_binance_klines():
    payload = [
        [1500000000000, "100.0", "102.0", "99.0", "101.5", "12.3", 1500000003600, "0", 10, "0", "0", "0"],
        [1500000003600, "101.5", "103.0", "101.0", "102.0", "9.1", 1500000007200, "0", 8, "0", "0", "0"],
    ]
    candles = parse_binance_klines(payload)
    assert len(candles) == 2
    assert candles[0].open == 100.0
    assert candles[0].close == 101.5
    assert candles[0].volume == 12.3


def test_parse_binance_klines_rejects_empty_and_malformed():
    with pytest.raises(ProviderError):
        parse_binance_klines([])
    with pytest.raises(ProviderError):
        parse_binance_klines([["not-a-number"]])


def test_parse_yahoo_chart_skips_null_bars():
    payload = {
        "chart": {
            "result": [{
                "timestamp": [1600000000, 1600003600, 1600007200],
                "indicators": {
                    "quote": [{
                        "open": [100.0, None, 102.0],
                        "high": [101.0, None, 103.0],
                        "low": [99.0, None, 101.0],
                        "close": [100.5, None, 102.5],
                        "volume": [100, None, 200],
                    }]
                },
            }]
        }
    }
    candles = parse_yahoo_chart(payload)
    assert len(candles) == 2
    assert candles[1].close == 102.5


def test_parse_yahoo_chart_rejects_bad_shape():
    with pytest.raises(ProviderError):
        parse_yahoo_chart({"chart": {"result": []}})


def test_candle_roundtrip_through_cache_dicts():
    candles = parse_binance_klines([[1500000000000, "1", "2", "0.5", "1.5", "3", 0, "0", 0, "0", "0", "0"]])
    restored = candles_from_dicts([candle_to_dict(c) for c in candles])
    assert restored[0] == candles[0]


# --------------------------------------------------------------------------
# Demo provider
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_demo_provider_deterministic_and_shaped():
    provider = DemoProvider()
    first = await provider.fetch_candles(Symbol.BTCUSDT, Timeframe.H1)
    second = await provider.fetch_candles(Symbol.BTCUSDT, Timeframe.H1)
    assert first == second
    assert len(first) == 500
    assert all(c.low <= c.high for c in first)
    assert all(c.open > 0 for c in first)
    assert all(c.volume >= 0 for c in first)
    for symbol in Symbol:
        assert provider.supports(symbol)


@pytest.mark.asyncio
async def test_demo_provider_timeframes_differ():
    provider = DemoProvider()
    hourly = await provider.fetch_candles(Symbol.BTCUSDT, Timeframe.H1)
    weekly = await provider.fetch_candles(Symbol.BTCUSDT, Timeframe.W1)
    # Candles are aligned to their timeframe: 1h steps of 60 minutes, weekly
    # steps of 7 days (plus a possible truncated leading candle).
    hourly_steps = {hourly[i + 1].epoch() - hourly[i].epoch() for i in range(len(hourly) - 1)}
    weekly_steps = {weekly[i + 1].epoch() - weekly[i].epoch() for i in range(len(weekly) - 1)}
    assert hourly_steps == {60 * 60}
    assert weekly_steps == {7 * 24 * 60 * 60}


# --------------------------------------------------------------------------
# Data manager (fallback behaviour)
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_manager_uses_demo_data_when_configured():
    settings = Settings(use_demo_data=True, chart_enabled=False)
    manager = MarketDataManager(object(), settings)  # no HTTP needed for demo
    batch = await manager.get_candles(Symbol.BTCUSDT, Timeframe.H1)
    assert batch.is_demo
    assert batch.source == "demo"
    sentiment = await manager.get_sentiment(Symbol.XAUUSD)
    assert sentiment.is_demo
    assert sentiment.fear_greed_value > 0


@pytest.mark.asyncio
async def test_manager_simulated_sources_are_stable_and_flagged():
    settings = Settings(use_demo_data=True, chart_enabled=False)
    manager = MarketDataManager(object(), settings)

    onchain = await manager.get_onchain(Symbol.ETHUSDT)
    assert onchain.is_demo is True
    assert onchain.mvrv is not None and onchain.mvrv > 0

    macro = await manager.get_macro()
    assert macro.is_demo is True
    assert -1 <= macro.rate_trend <= 1

    scan = await manager.get_sniper_scan()
    assert scan.is_demo is True
    assert len(scan.tokens) >= 2
    assert all(t.liquidity_usd > 0 for t in scan.tokens)

    # Deterministic: repeated calls return identical values.
    assert (await manager.get_onchain(Symbol.ETHUSDT)) == onchain


@pytest.mark.asyncio
async def test_sniper_scan_disabled_returns_empty():
    settings = Settings(use_demo_data=True, sniper_enabled=False, chart_enabled=False)
    manager = MarketDataManager(object(), settings)
    scan = await manager.get_sniper_scan()
    assert scan.tokens == ()
    assert scan.source == "disabled"


@pytest.mark.asyncio
async def test_manager_raises_when_no_provider_and_no_fallback():
    settings = Settings(use_demo_data=False, demo_fallback=False, chart_enabled=False)
    manager = MarketDataManager(object(), settings)

    class FailingProvider:
        name = "failing"
        is_demo = False

        def supports(self, symbol: Symbol) -> bool:
            return True

        async def fetch_candles(self, symbol, timeframe, limit=500):
            raise ProviderError("boom")

    manager._candle_chain = [FailingProvider()]  # type: ignore[assignment]
    with pytest.raises(ProviderError):
        await manager.get_candles(Symbol.BTCUSDT, Timeframe.H1)


@pytest.mark.asyncio
async def test_manager_sentiment_requires_source_when_demo_disabled():
    settings = Settings(use_demo_data=False, demo_fallback=False, chart_enabled=False)
    manager = MarketDataManager(object(), settings)

    class FailingNews:
        async def fetch(self, symbol: Symbol) -> None:
            raise ProviderError("news source down")

    manager._news = FailingNews()  # type: ignore[assignment]
    with pytest.raises(ProviderError):
        await manager.get_sentiment(Symbol.BTCUSDT)
