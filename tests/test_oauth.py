"""Tests for Google OAuth helpers and endpoints."""

from __future__ import annotations

from aiohttp.test_utils import TestClient, TestServer

from tradingbot.api.oauth import (
    build_authorize_url,
    create_session_token,
    verify_session_token,
)
from tradingbot.api.server import create_web_app
from tradingbot.config import Settings


def test_authorize_url_contains_params() -> None:
    settings = Settings(
        google_client_id="cid.apps.googleusercontent.com",
        google_client_secret="secret",
        auth_base_url="https://auth.pkay.fun",
    )
    url = build_authorize_url(settings, "state123")
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=cid.apps.googleusercontent.com" in url
    assert "state=state123" in url
    assert "scope=openid+email+profile" in url
    assert (
        "redirect_uri=https%3A%2F%2Fauth.pkay.fun%2Fapi%2Fv3%2Fauth%2Fgoogle%2Fcallback"
        in url
    )


def test_google_redirect_uri() -> None:
    settings = Settings(auth_base_url="https://auth.pkay.fun/")
    assert (
        settings.google_redirect_uri
        == "https://auth.pkay.fun/api/v3/auth/google/callback"
    )


def test_session_token_roundtrip() -> None:
    settings = Settings(session_secret="test-secret")
    token = create_session_token(settings, 42)
    assert verify_session_token(settings, token) == 42
    assert verify_session_token(settings, "garbage") is None
    assert verify_session_token(settings, None) is None
    assert verify_session_token(settings, token[:-2] + "xx") is None
    assert verify_session_token(Settings(session_secret="other"), token) is None


async def test_google_login_requires_config() -> None:
    app = create_web_app(object(), Settings())
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.get("/api/v3/auth/google", allow_redirects=False)
        assert resp.status == 503
    finally:
        await client.close()


async def test_google_login_redirects_when_configured() -> None:
    settings = Settings(google_client_id="cid", google_client_secret="secret")
    app = create_web_app(object(), settings)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.get("/api/v3/auth/google", allow_redirects=False)
        assert resp.status == 302
        assert resp.headers["Location"].startswith("https://accounts.google.com/")
    finally:
        await client.close()


async def test_auth_me_rejects_without_token() -> None:
    app = create_web_app(object(), Settings(session_secret="s"))
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.get("/api/v3/auth/me")
        assert resp.status == 401
    finally:
        await client.close()
