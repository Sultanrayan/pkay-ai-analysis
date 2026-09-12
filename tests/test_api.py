"""Tests for the public v3 API (agents endpoint, auth and serialization)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from aiohttp.test_utils import TestClient, TestServer

from tradingbot.api.agents import FUNCTIONS, functions_response
from tradingbot.api.auth import check_api_key, extract_bearer
from tradingbot.api.serializers import report_to_dict
from tradingbot.api.server import create_web_app
from tradingbot.config import Settings

# --- functions catalogue ---------------------------------------------------


def test_functions_response_returns_functions_only() -> None:
    payload = functions_response(None)

    assert payload["endpoint"] == "/api/v3/agents"
    assert payload["count"] == len(FUNCTIONS)
    # functions-only: no analysis result, no model anywhere
    assert "model" not in payload
    assert "agents" not in payload
    for tool in payload["functions"]:
        assert set(tool) == {"name", "description", "parameters"}
        assert tool["parameters"]["required"] == ["symbol", "timeframe"]


def test_functions_response_filters_by_id_and_name() -> None:
    payload = functions_response(["technical", "scan_sniper"])
    names = {tool["name"] for tool in payload["functions"]}
    assert names == {"analyze_technical", "scan_sniper"}


def test_functions_response_rejects_unknown() -> None:
    try:
        functions_response(["not_a_function"])
    except ValueError as exc:
        assert "Unknown function" in str(exc)
    else:  # pragma: no cover - the call above must raise
        raise AssertionError("expected ValueError")


# --- auth ------------------------------------------------------------------


def test_check_api_key_open_when_unconfigured() -> None:
    assert check_api_key(None, ()) is True


def test_check_api_key_requires_match() -> None:
    keys = ("pk_live_abc",)
    assert check_api_key("pk_live_abc", keys) is True
    assert check_api_key("wrong", keys) is False
    assert check_api_key(None, keys) is False


def test_extract_bearer() -> None:
    assert extract_bearer("Bearer pk_live_abc") == "pk_live_abc"
    assert extract_bearer("bearer  pk_live_abc ") == "pk_live_abc"
    assert extract_bearer("Basic abc") is None
    assert extract_bearer(None) is None


# --- serialization ---------------------------------------------------------


def test_report_to_dict_shape() -> None:
    report = SimpleNamespace(
        symbol=SimpleNamespace(value="BTCUSDT"),
        timeframe=SimpleNamespace(value="1h"),
        final_signal="BUY",
        final_confidence=82.0,
        final_summary="bullish",
        current_price=64120.5,
        decision=SimpleNamespace(total_score=58.0, team_scores={"technical": 0.35}),
        technical=SimpleNamespace(score=52.2),
        volume=SimpleNamespace(score=41.0),
        volatility=SimpleNamespace(score=28.5),
        pattern=SimpleNamespace(score=47.1),
        sentiment=SimpleNamespace(score=29.0),
        onchain=SimpleNamespace(score=23.2),
        macro=SimpleNamespace(score=17.4),
        correlation=SimpleNamespace(score=12.0),
        risk=SimpleNamespace(
            score=40.6,
            stop_loss=62900.0,
            take_profit=66100.0,
            position_size_pct=2.5,
            atr=890.0,
            volatility_label="Medium",
        ),
        sniper=SimpleNamespace(opportunity_score=31.0),
        llm=None,
        any_demo_data=False,
        response_time_ms=123,
        created_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
    )

    payload = report_to_dict(report)

    assert payload["signal"] == "BUY"
    assert payload["agents"]["sniper"] == 31.0
    assert payload["risk"]["stop_loss"] == 62900.0
    assert payload["llm_enhanced"] is False
    assert payload["generated_at"].startswith("2026-09-11")


# --- HTTP integration ------------------------------------------------------


async def _client(keys: tuple[str, ...] = ("pk_test",)) -> TestClient:
    app = create_web_app(object(), Settings(api_keys=keys))
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


async def test_agents_endpoint_functions_only() -> None:
    client = await _client()
    try:
        resp = await client.post(
            "/api/v3/agents",
            json={"functions": ["technical", "risk"]},
            headers={"Authorization": "Bearer pk_test"},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["count"] == 2
        assert data["endpoint"] == "/api/v3/agents"
        assert "model" not in data
    finally:
        await client.close()


async def test_agents_endpoint_rejects_user_model() -> None:
    client = await _client()
    try:
        resp = await client.post(
            "/api/v3/agents",
            json={"model": "gpt-6-astra"},
            headers={"Authorization": "Bearer pk_test"},
        )
        assert resp.status == 400
    finally:
        await client.close()


async def test_agents_endpoint_requires_key() -> None:
    client = await _client()
    try:
        resp = await client.post("/api/v3/agents", json={})
        assert resp.status == 401
    finally:
        await client.close()


async def test_health() -> None:
    client = await _client()
    try:
        resp = await client.get("/health")
        assert resp.status == 200
        assert (await resp.json())["status"] == "ok"
    finally:
        await client.close()
