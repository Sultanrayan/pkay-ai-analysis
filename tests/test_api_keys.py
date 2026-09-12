"""Tests for API key helpers, DB-backed API storage and key authentication."""

from __future__ import annotations

from types import SimpleNamespace

from aiohttp.test_utils import TestClient, TestServer

from tradingbot.api.keys import generate_api_key, hash_api_key, key_prefix
from tradingbot.api.server import create_web_app
from tradingbot.config import Settings
from tradingbot.storage.repository import InMemoryStorage

# --- key helpers -----------------------------------------------------------


def test_generate_and_hash_key() -> None:
    key = generate_api_key("live")
    assert key.startswith("pk_live_")
    assert len(key) > 20

    digest = hash_api_key(key)
    assert len(digest) == 64
    assert digest == hash_api_key(key)  # stable
    assert digest != key
    assert key_prefix(key) == key[:12]


# --- storage ---------------------------------------------------------------


async def test_api_user_and_keys_roundtrip() -> None:
    storage = InMemoryStorage()
    user = await storage.get_or_create_api_user(
        "google-123", email="a@b.com", name="Ada"
    )
    assert user.id == 1
    again = await storage.get_or_create_api_user("google-123")
    assert again.id == 1  # idempotent

    raw = generate_api_key("live")
    key = await storage.create_api_key(
        key_hash=hash_api_key(raw),
        key_prefix=key_prefix(raw),
        name="prod",
        environment="live",
        scopes=("analyze",),
        user_id=user.id,
    )
    found = await storage.get_api_key_by_hash(hash_api_key(raw))
    assert found is not None and found.id == key.id
    assert found.active
    assert found.scopes == ("analyze",)

    await storage.touch_api_key(key.id)
    assert key.request_count == 1
    assert key.last_used_at is not None

    await storage.revoke_api_key(key.id)
    assert not key.active
    # still retrievable, but revoked
    assert await storage.get_api_key_by_hash(hash_api_key(raw)) is not None
    assert len(await storage.list_api_keys(user.id)) == 1


async def test_api_usage_summary() -> None:
    storage = InMemoryStorage()
    await storage.record_api_usage(
        key_id=1, endpoint="/api/v3/analyze", status_code=200
    )
    await storage.record_api_usage(
        key_id=1, endpoint="/api/v3/analyze", status_code=500
    )
    summary = await storage.api_usage_summary(key_id=1)
    assert summary.total == 2
    assert summary.today == 2
    assert summary.errors == 1
    assert summary.success_rate == 50.0


# --- endpoint auth + usage wiring ------------------------------------------


async def _client_with_storage(storage: InMemoryStorage) -> TestClient:
    application = SimpleNamespace(bot_data={"services": SimpleNamespace(storage=storage)})
    app = create_web_app(application, Settings(api_keys=()))
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


async def test_db_key_authenticates_and_records_usage() -> None:
    storage = InMemoryStorage()
    raw = generate_api_key("live")
    await storage.create_api_key(
        key_hash=hash_api_key(raw), key_prefix=key_prefix(raw), name="prod"
    )
    client = await _client_with_storage(storage)
    try:
        resp = await client.post(
            "/api/v3/agents",
            json={},
            headers={"Authorization": f"Bearer {raw}"},
        )
        assert resp.status == 200

        summary = await storage.api_usage_summary()
        assert summary.total == 1
        assert summary.errors == 0
    finally:
        await client.close()


async def test_unknown_db_key_is_rejected() -> None:
    storage = InMemoryStorage()
    client = await _client_with_storage(storage)
    try:
        resp = await client.post(
            "/api/v3/agents",
            json={},
            headers={"Authorization": "Bearer pk_live_not_a_real_key"},
        )
        assert resp.status == 401
    finally:
        await client.close()
