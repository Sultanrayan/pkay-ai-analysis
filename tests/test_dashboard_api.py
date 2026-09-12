"""Tests for the dashboard API (keys + usage) backed by storage."""

from __future__ import annotations

from types import SimpleNamespace

from aiohttp.test_utils import TestClient, TestServer

from tradingbot.api.oauth import create_session_token
from tradingbot.api.passwords import hash_password, verify_password
from tradingbot.api.server import create_web_app
from tradingbot.config import Settings
from tradingbot.storage.repository import InMemoryStorage


async def _client(storage: InMemoryStorage, settings: Settings) -> TestClient:
    application = SimpleNamespace(
        bot_data={"services": SimpleNamespace(storage=storage)}
    )
    app = create_web_app(application, settings)
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


async def test_keys_require_session() -> None:
    storage = InMemoryStorage()
    client = await _client(storage, Settings(session_secret="s"))
    try:
        resp = await client.get("/api/v3/keys")
        assert resp.status == 401
    finally:
        await client.close()


async def test_keys_crud_and_usage() -> None:
    storage = InMemoryStorage()
    user = await storage.get_or_create_api_user(
        "sub-1", email="a@b.com", name="Ada"
    )
    settings = Settings(session_secret="s")
    token = create_session_token(settings, user.id)
    headers = {"Authorization": f"Bearer {token}"}

    client = await _client(storage, settings)
    try:
        # create
        resp = await client.post(
            "/api/v3/keys",
            json={"name": "prod", "environment": "live", "scopes": ["analyze"]},
            headers=headers,
        )
        assert resp.status == 201
        created = await resp.json()
        assert created["secret"].startswith("pk_live_")
        assert created["status"] == "active"
        key_id = created["id"]

        # list (secret never returned)
        resp = await client.get("/api/v3/keys", headers=headers)
        data = await resp.json()
        assert len(data["keys"]) == 1
        assert data["keys"][0]["name"] == "prod"
        assert "secret" not in data["keys"][0]

        # usage empty
        resp = await client.get("/api/v3/usage", headers=headers)
        usage = await resp.json()
        assert usage["summary"]["total"] == 0
        assert len(usage["series"]) == 14
        assert usage["by_model"] == []

        # record usage -> reflected in summary/breakdown/recent
        await storage.record_api_usage(
            key_id=key_id,
            endpoint="/api/v3/analyze",
            status_code=200,
            symbol="BTCUSDT",
            timeframe="15m",
            model="deepseek-v4-flash",
            latency_ms=120,
        )
        resp = await client.get("/api/v3/usage", headers=headers)
        usage = await resp.json()
        assert usage["summary"]["total"] == 1
        assert usage["by_model"][0]["label"] == "deepseek-v4-flash"
        assert usage["by_endpoint"][0]["label"] == "/api/v3/analyze"
        assert usage["by_symbol"][0]["label"] == "BTCUSDT"
        assert usage["recent"][0]["endpoint"] == "/api/v3/analyze"
        assert usage["series"][-1]["requests"] == 1

        # revoke
        resp = await client.post(
            f"/api/v3/keys/{key_id}/revoke", headers=headers
        )
        assert resp.status == 200
        assert (await storage.list_api_keys(user.id))[0].active is False

        # delete
        resp = await client.delete(f"/api/v3/keys/{key_id}", headers=headers)
        assert resp.status == 200
        assert await storage.list_api_keys(user.id) == []
    finally:
        await client.close()


async def test_settings_roundtrip() -> None:
    storage = InMemoryStorage()
    user = await storage.get_or_create_api_user("sub-2")
    settings = Settings(session_secret="s")
    token = create_session_token(settings, user.id)
    headers = {"Authorization": f"Bearer {token}"}

    client = await _client(storage, settings)
    try:
        resp = await client.get("/api/v3/settings", headers=headers)
        data = await resp.json()
        assert data["theme"] == "dark"
        assert data["language"] == "en"

        resp = await client.put(
            "/api/v3/settings",
            json={
                "theme": "light",
                "language": "kh",
                "currency": "eur",
                "timezone": "ict",
            },
            headers=headers,
        )
        assert resp.status == 200
        updated = await resp.json()
        assert updated["theme"] == "light"
        assert updated["language"] == "kh"
        assert updated["currency"] == "eur"
        assert updated["timezone"] == "ict"

        # persisted
        resp = await client.get("/api/v3/settings", headers=headers)
        assert (await resp.json())["theme"] == "light"
    finally:
        await client.close()


async def test_change_password() -> None:
    storage = InMemoryStorage()
    user = await storage.get_or_create_api_user("sub-3")
    settings = Settings(session_secret="s")
    token = create_session_token(settings, user.id)
    headers = {"Authorization": f"Bearer {token}"}

    client = await _client(storage, settings)
    try:
        resp = await client.post(
            "/api/v3/auth/password",
            json={"new_password": "short"},
            headers=headers,
        )
        assert resp.status == 400

        resp = await client.post(
            "/api/v3/auth/password",
            json={"new_password": "supersecret"},
            headers=headers,
        )
        assert resp.status == 200

        resp = await client.post(
            "/api/v3/auth/password",
            json={"current_password": "nope", "new_password": "anothersecret"},
            headers=headers,
        )
        assert resp.status == 400

        resp = await client.post(
            "/api/v3/auth/password",
            json={
                "current_password": "supersecret",
                "new_password": "anothersecret",
            },
            headers=headers,
        )
        assert resp.status == 200
    finally:
        await client.close()


def test_password_hash_roundtrip() -> None:
    stored = hash_password("hunter2secret")
    assert stored != "hunter2secret"
    assert verify_password("hunter2secret", stored)
    assert not verify_password("wrong", stored)
    assert not verify_password("hunter2secret", None)
