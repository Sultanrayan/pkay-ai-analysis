"""Tests for the DeepSeek-V4-Flash enrichment client (offline, mocked)."""

from __future__ import annotations

import httpx
import pytest

from tradingbot.config import Settings
from tradingbot.llm import DeepSeekClient, _extract_json


def _settings(**overrides) -> Settings:
    defaults = dict(deepseek_api_key="test-key", deepseek_timeout=5.0)
    defaults.update(overrides)
    return Settings(**defaults)


def _client(handler) -> DeepSeekClient:
    transport = httpx.MockTransport(handler)
    return DeepSeekClient(_settings(), client=httpx.AsyncClient(transport=transport))


def _json_response(payload: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": payload}}]},
    )


def test_disabled_without_api_key():
    client = DeepSeekClient(Settings(deepseek_api_key=""))
    assert client.enabled() is False


@pytest.mark.asyncio
async def test_disabled_client_returns_none():
    client = DeepSeekClient(Settings(deepseek_api_key=""))
    result = await client.enhance({"asset": "BTCUSDT"})
    assert result is None


@pytest.mark.asyncio
async def test_enhance_returns_valid_result():
    client = _client(lambda request: _json_response(
        '{"signal": "BUY", "confidence": 87, "summary": "Strong trend with volume."}'
    ))
    result = await client.enhance({"asset": "BTCUSDT"})
    assert result is not None
    assert result.signal == "BUY"
    assert result.confidence == 87.0
    assert "Strong trend" in result.summary
    assert result.model == "deepseek-v4-flash"
    await client.close()


@pytest.mark.asyncio
async def test_enhance_tolerates_code_fenced_json():
    client = _client(lambda request: _json_response(
        '```json\n{"signal": "HOLD", "confidence": 50, "summary": "Neutral."}\n```'
    ))
    result = await client.enhance({"asset": "ETHUSDT"})
    assert result is not None and result.signal == "HOLD"
    await client.close()


@pytest.mark.asyncio
async def test_enhance_falls_back_on_http_error():
    def boom(request):
        raise httpx.ConnectError("network down")

    client = _client(boom)
    result = await client.enhance({"asset": "BTCUSDT"})
    assert result is None  # graceful degradation
    await client.close()


@pytest.mark.asyncio
async def test_enhance_rejects_invalid_signal():
    client = _client(lambda request: _json_response(
        '{"signal": "MAYBE", "confidence": 99, "summary": "?"}'
    ))
    result = await client.enhance({"asset": "BTCUSDT"})
    assert result is None
    await client.close()


@pytest.mark.asyncio
async def test_enhance_rejects_malformed_body():
    client = _client(lambda request: _json_response("not json at all"))
    result = await client.enhance({"asset": "BTCUSDT"})
    assert result is None
    await client.close()


def test_extract_json_handles_prose_and_fences():
    assert _extract_json('Sure! {"signal": "BUY"} done') == {"signal": "BUY"}
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert _extract_json("no json here") is None
    assert _extract_json('{"unclosed": ') is None