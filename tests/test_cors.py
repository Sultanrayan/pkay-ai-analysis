"""Tests for CORS handling on the public API."""

from __future__ import annotations

from aiohttp.test_utils import TestClient, TestServer

from tradingbot.api.server import create_web_app
from tradingbot.config import Settings


async def test_cors_preflight_allows_configured_origin() -> None:
    settings = Settings(cors_origins=("https://developer.pkay.fun",))
    app = create_web_app(object(), settings)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.options(
            "/api/v3/keys",
            headers={
                "Origin": "https://developer.pkay.fun",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status == 204
        assert (
            resp.headers["Access-Control-Allow-Origin"]
            == "https://developer.pkay.fun"
        )
        assert "Authorization" in resp.headers["Access-Control-Allow-Headers"]
    finally:
        await client.close()


async def test_cors_preflight_rejects_unknown_origin() -> None:
    settings = Settings(cors_origins=("https://developer.pkay.fun",))
    app = create_web_app(object(), settings)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.options(
            "/api/v3/keys",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "Access-Control-Allow-Origin" not in resp.headers
    finally:
        await client.close()


async def test_cors_headers_on_actual_request() -> None:
    settings = Settings(cors_origins=("https://developer.pkay.fun",))
    app = create_web_app(object(), settings)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.get(
            "/health", headers={"Origin": "https://developer.pkay.fun"}
        )
        assert resp.status == 200
        assert (
            resp.headers["Access-Control-Allow-Origin"]
            == "https://developer.pkay.fun"
        )
    finally:
        await client.close()
