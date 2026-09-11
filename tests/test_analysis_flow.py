"""End-to-end tests: analysis runner (demo data) -> report -> history row."""

from __future__ import annotations

import httpx
import pytest

from tradingbot.analysis.runner import AnalysisRunner
from tradingbot.config import Settings
from tradingbot.data.manager import MarketDataManager
from tradingbot.domain import Symbol, Timeframe
from tradingbot.storage.models import history_row_from_report
from tradingbot.storage.repository import InMemoryStorage


@pytest.fixture
async def runner() -> AnalysisRunner:
    settings = Settings(use_demo_data=True, chart_enabled=False)
    client = httpx.AsyncClient()
    data = MarketDataManager(client, settings)
    yield AnalysisRunner(data, settings)
    await client.aclose()


@pytest.mark.asyncio
async def test_full_analysis_produces_report(runner):
    report = await runner.analyze(Symbol.BTCUSDT, Timeframe.H1)
    assert report.symbol == Symbol.BTCUSDT
    assert report.current_price > 0
    assert report.is_demo_data is True
    assert report.response_time_ms >= 0
    assert report.candles and len(report.candles) >= 200

    # Every agent contributed a bounded score.
    agents = (
        report.technical, report.volume, report.volatility, report.pattern,
        report.sentiment, report.onchain, report.macro, report.risk,
        report.correlation,
    )
    for result in agents:
        assert -100 <= result.score <= 100
    assert 0 <= report.sniper.opportunity_score <= 100

    # Technical internals available for the report body.
    assert report.technical.rsi is not None
    assert report.technical.ma_50 is not None

    # Risk setup is a coherent long/short/neutral geometry.
    assert report.risk.atr > 0
    assert report.risk.stop_loss is not None

    # Decision signal text and summary exist.
    assert report.decision.signal in {"BUY", "SELL", "HOLD"}
    assert report.decision.summary
    assert 0 <= report.decision.confidence <= 100
    assert report.final_signal == report.decision.signal  # no LLM configured

    # Sentiment/onchain/macro/sniper provenance recorded.
    assert report.sentiment.is_demo is True
    assert report.onchain.is_demo is True
    assert report.macro.is_demo is True
    assert report.sniper.is_demo is True
    assert "price" in report.demo_sources


@pytest.mark.asyncio
async def test_analysis_is_stable_across_runs(runner):
    first = await runner.analyze(Symbol.XAUUSD, Timeframe.D1)
    second = await runner.analyze(Symbol.XAUUSD, Timeframe.D1)
    assert first.decision.total_score == second.decision.total_score
    assert first.current_price == second.current_price
    assert first.sniper.opportunity_score == second.sniper.opportunity_score


@pytest.mark.asyncio
async def test_every_asset_analyzable_with_demo_data(runner):
    for symbol in Symbol:
        report = await runner.analyze(symbol, Timeframe.H4)
        assert report.current_price > 0
        assert report.decision.signal in {"BUY", "SELL", "HOLD"}


@pytest.mark.asyncio
async def test_report_maps_to_history_row(runner):
    report = await runner.analyze(Symbol.BTCUSDT, Timeframe.H4)
    row = history_row_from_report(report, user_id=123)
    assert row.symbol == "BTCUSDT"
    assert row.timeframe == "4h"
    assert row.signal == report.final_signal
    assert row.total_score == round(report.decision.total_score)
    assert row.technical_score == round(report.technical.score)
    assert row.volume_score == round(report.volume.score)
    assert row.onchain_score == round(report.onchain.score)
    assert row.sniper_score == round(report.sniper.opportunity_score)
    assert row.confidence == report.final_confidence
    assert row.summary == report.final_summary
    assert row.llm_enhanced is False
    assert row.agent_contributions == report.decision.contributions

    storage = InMemoryStorage()
    await storage.get_or_create_user(123)
    row_id = await storage.add_analysis(row)
    fetched = await storage.get_history_row(123, row_id)
    assert fetched is not None
    assert fetched.signal == report.final_signal
    assert fetched.current_price == pytest.approx(report.current_price)
    assert fetched.confidence == report.final_confidence