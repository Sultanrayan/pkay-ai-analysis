"""aiohttp HTTP layer: Telegram webhook + public JSON API (v3).

Mounted in the same process as the Telegram bot. ``create_web_app`` wires the
routes and the handlers read the runtime service bag from the Telegram
application's ``bot_data`` (populated by ``post_init``).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from aiohttp import web
from telegram import Update

from ..config import Settings
from ..domain import Symbol, Timeframe
from ..webhook_security import verify_telegram_signature
from .agents import functions_response
from .auth import check_api_key, extract_bearer
from .keys import generate_api_key, hash_api_key, key_prefix
from .oauth import (
    build_authorize_url,
    create_session_token,
    exchange_code,
    fetch_userinfo,
    new_state,
    verify_session_token,
)
from .passwords import hash_password, verify_password
from .serializers import report_to_dict

logger = logging.getLogger(__name__)

#: aiohttp app keys (typed to avoid NotAppKeyWarning).
TELEGRAM_APPLICATION_KEY: web.AppKey = web.AppKey("telegram_application", object)
SETTINGS_KEY: web.AppKey = web.AppKey("settings", Settings)

#: Reject request bodies larger than this (protects the process).
MAX_BODY_BYTES = 64 * 1024

#: Keys that are always returned by ``/api/v3/analyze`` regardless of ``data``.
_CORE_KEYS = frozenset(
    {
        "symbol",
        "timeframe",
        "model",
        "signal",
        "score",
        "confidence",
        "current_price",
        "summary",
        "llm_enhanced",
        "demo_data",
        "response_time_ms",
        "generated_at",
    }
)


def _error(status: int, message: str) -> web.Response:
    return web.json_response({"error": message}, status=status)


def _cors_headers(origin: str | None, settings: Settings) -> dict[str, str]:
    allowed = settings.cors_origins
    if allowed and origin and origin.rstrip("/") not in allowed:
        return {}
    return {
        "Access-Control-Allow-Origin": origin or "*",
        "Vary": "Origin",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Max-Age": "86400",
    }


@web.middleware
async def cors_middleware(request: web.Request, handler: Any) -> web.Response:
    if request.method == "OPTIONS":
        response: web.Response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as exc:
            response = exc
    settings: Settings = request.app[SETTINGS_KEY]
    for key, value in _cors_headers(request.headers.get("Origin"), settings).items():
        response.headers[key] = value
    return response


def _services(request: web.Request) -> Any:
    application = request.app.get(TELEGRAM_APPLICATION_KEY)
    bot_data = getattr(application, "bot_data", None)
    return bot_data.get("services") if isinstance(bot_data, dict) else None


async def _authenticate(request: web.Request) -> tuple[bool, Any]:
    """Resolve the caller's API key.

    Static keys from ``PKAY_API_KEYS`` are accepted first (backwards
    compatible), then hashed keys stored in the database. Returns
    ``(authorized, key_record)``; ``key_record`` is ``None`` for static keys
    or open (dev) mode.
    """
    settings: Settings = request.app[SETTINGS_KEY]
    token = extract_bearer(request.headers.get("Authorization"))

    if settings.api_keys:
        if check_api_key(token, settings.api_keys):
            return True, None
    elif token is None:
        # No keys configured at all: open dev mode.
        return True, None

    if token:
        services = _services(request)
        storage = getattr(services, "storage", None)
        if storage is not None:
            try:
                record = await storage.get_api_key_by_hash(hash_api_key(token))
            except Exception:
                logger.debug("API key lookup failed", exc_info=True)
                record = None
            if record is not None and record.revoked_at is None:
                return True, record
    return False, None


async def _record_usage(
    request: web.Request,
    key: Any,
    endpoint: str,
    status_code: int,
    started: float,
    **meta: Any,
) -> None:
    services = _services(request)
    storage = getattr(services, "storage", None)
    if storage is None:
        return
    key_id = getattr(key, "id", None)
    latency_ms = int((time.perf_counter() - started) * 1000)
    try:
        await storage.record_api_usage(
            key_id=key_id,
            endpoint=endpoint,
            status_code=status_code,
            latency_ms=latency_ms,
            **meta,
        )
        if key_id is not None:
            await storage.touch_api_key(key_id)
    except Exception:
        logger.debug("Usage recording failed", exc_info=True)


async def _finish(
    request: web.Request,
    key: Any,
    endpoint: str,
    response: web.Response,
    started: float,
    **meta: Any,
) -> web.Response:
    await _record_usage(request, key, endpoint, response.status, started, **meta)
    return response


async def _read_json(request: web.Request) -> dict[str, Any] | web.Response:
    if request.content_type != "application/json":
        return _error(415, "Expected application/json")
    try:
        body = await request.json()
    except Exception:
        return _error(400, "Invalid JSON body")
    if not isinstance(body, dict):
        return _error(400, "JSON body must be an object")
    return body


# --- Telegram webhook ------------------------------------------------------


async def telegram_webhook(request: web.Request) -> web.Response:
    application = request.app[TELEGRAM_APPLICATION_KEY]
    settings: Settings = request.app[SETTINGS_KEY]

    body = await request.read()
    if not verify_telegram_signature(request.headers, body, settings.telegram_bot_token):
        logger.warning("Rejected Telegram webhook: invalid secret token")
        return _error(401, "Invalid webhook signature")

    try:
        data = await request.json()
    except Exception:
        return _error(400, "Invalid JSON body")

    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.json_response({"ok": True})


# --- API: agents (functions only) ------------------------------------------


async def agents_endpoint(request: web.Request) -> web.Response:
    endpoint = "/api/v3/agents"
    started = time.perf_counter()
    ok, key = await _authenticate(request)
    if not ok:
        return await _finish(
            request, key, endpoint, _error(401, "Missing or invalid API key"), started
        )

    body = await _read_json(request)
    if isinstance(body, web.Response):
        return await _finish(request, key, endpoint, body, started)

    # This endpoint is functions-only: it must never accept a user model.
    if "model" in body:
        return await _finish(
            request,
            key,
            endpoint,
            _error(400, "This endpoint does not accept a model"),
            started,
        )

    fmt = body.get("format", "tools")
    if fmt not in ("tools", "json"):
        return await _finish(
            request,
            key,
            endpoint,
            _error(400, "format must be 'tools' or 'json'"),
            started,
        )

    try:
        payload = functions_response(body.get("functions"), fmt)
    except ValueError as exc:
        return await _finish(request, key, endpoint, _error(400, str(exc)), started)
    return await _finish(
        request, key, endpoint, web.json_response(payload), started
    )


# --- API: analyze ----------------------------------------------------------


async def analyze_endpoint(request: web.Request) -> web.Response:
    endpoint = "/api/v3/analyze"
    started = time.perf_counter()
    ok, key = await _authenticate(request)
    if not ok:
        return await _finish(
            request, key, endpoint, _error(401, "Missing or invalid API key"), started
        )

    body = await _read_json(request)
    if isinstance(body, web.Response):
        return await _finish(request, key, endpoint, body, started)

    symbol = Symbol.parse(str(body.get("symbol", "")))
    timeframe = Timeframe.parse(str(body.get("timeframe", "")))
    meta: dict[str, Any] = {
        "symbol": symbol.value if symbol else None,
        "timeframe": timeframe.value if timeframe else None,
    }
    if symbol is None or timeframe is None:
        return await _finish(
            request,
            key,
            endpoint,
            _error(400, "A valid Data Pair (symbol + timeframe) is required"),
            started,
            **meta,
        )

    services = _services(request)
    if services is None:
        return await _finish(
            request, key, endpoint, _error(503, "Service not ready"), started, **meta
        )

    try:
        report = await services.runner.analyze(symbol, timeframe)
    except Exception:
        logger.exception("Analysis failed for %s %s", symbol.value, timeframe.value)
        return await _finish(
            request, key, endpoint, _error(500, "Analysis failed"), started, **meta
        )

    payload = report_to_dict(report)
    model = body.get("model") or request.app[SETTINGS_KEY].deepseek_model
    payload["model"] = model
    meta["model"] = model

    requested = body.get("data")
    if isinstance(requested, list) and requested:
        allowed = _CORE_KEYS | {str(item) for item in requested}
        payload = {key_name: value for key_name, value in payload.items() if key_name in allowed}

    return await _finish(
        request, key, endpoint, web.json_response(payload), started, **meta
    )


# --- API: Google OAuth (login / register) ----------------------------------


async def google_login(request: web.Request) -> web.Response:
    settings: Settings = request.app[SETTINGS_KEY]
    if not settings.google_client_id or not settings.google_client_secret:
        return _error(503, "Google sign-in is not configured")

    state = new_state()
    response = web.HTTPFound(build_authorize_url(settings, state))
    response.set_cookie(
        "oauth_state",
        state,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=600,
        path="/",
    )
    raise response


async def google_callback(request: web.Request) -> web.Response:
    settings: Settings = request.app[SETTINGS_KEY]

    if request.query.get("error"):
        return _error(400, f"Google sign-in failed: {request.query['error']}")
    state = request.query.get("state")
    if not state or state != request.cookies.get("oauth_state"):
        return _error(400, "Invalid OAuth state")
    code = request.query.get("code")
    if not code:
        return _error(400, "Missing authorization code")

    services = _services(request)
    storage = getattr(services, "storage", None)
    if storage is None:
        return _error(503, "Service not ready")

    http = getattr(services, "http", None)
    owns_client = http is None
    if http is None:
        import httpx

        http = httpx.AsyncClient(timeout=15.0)
    try:
        tokens = await exchange_code(settings, http, code)
        userinfo = await fetch_userinfo(http, tokens["access_token"])
    except Exception:
        logger.exception("Google token exchange failed")
        return _error(400, "Google sign-in failed")
    finally:
        if owns_client:
            await http.aclose()

    google_sub = str(userinfo.get("sub") or "")
    if not google_sub:
        return _error(400, "Google account did not return a subject id")

    user = await storage.get_or_create_api_user(
        google_sub,
        email=userinfo.get("email"),
        name=userinfo.get("name"),
        picture=userinfo.get("picture"),
    )
    token = create_session_token(settings, user.id)

    wants_json = request.query.get("format") == "json" or "application/json" in (
        request.headers.get("Accept", "")
    )
    if wants_json:
        response: web.Response = web.json_response(
            {
                "token": token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "picture": user.picture,
                    "plan": user.plan,
                },
            }
        )
        response.del_cookie("oauth_state", path="/")
        return response

    base = settings.frontend_url.rstrip("/")
    location = f"{base}/dashboard?token={token}" if base else f"/?token={token}"
    redirect = web.HTTPFound(location)
    redirect.del_cookie("oauth_state", path="/")
    raise redirect


async def auth_me(request: web.Request) -> web.Response:
    settings: Settings = request.app[SETTINGS_KEY]
    token = extract_bearer(request.headers.get("Authorization"))
    user_id = verify_session_token(settings, token)
    if user_id is None:
        return _error(401, "Not authenticated")

    services = _services(request)
    storage = getattr(services, "storage", None)
    user = await storage.get_api_user(user_id) if storage is not None else None
    if user is None:
        return _error(401, "Not authenticated")

    return web.json_response(
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "plan": user.plan,
        }
    )


# --- API: dashboard (session-authenticated) --------------------------------


def _serialize_key(key: Any) -> dict[str, Any]:
    return {
        "id": key.id,
        "name": key.name,
        "environment": key.environment,
        "scopes": list(key.scopes),
        "key_prefix": key.key_prefix,
        "status": "active" if key.active else "revoked",
        "created_at": key.created_at.isoformat() if key.created_at else None,
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        "request_count": key.request_count,
    }


async def _current_user(request: web.Request) -> Any:
    settings: Settings = request.app[SETTINGS_KEY]
    token = extract_bearer(request.headers.get("Authorization"))
    user_id = verify_session_token(settings, token)
    if user_id is None:
        return None
    services = _services(request)
    storage = getattr(services, "storage", None)
    if storage is None:
        return None
    return await storage.get_api_user(user_id)


async def keys_endpoint(request: web.Request) -> web.Response:
    user = await _current_user(request)
    if user is None:
        return _error(401, "Sign in required")
    storage = _services(request).storage
    keys = await storage.list_api_keys(user.id)
    return web.json_response({"keys": [_serialize_key(key) for key in keys]})


async def create_key_endpoint(request: web.Request) -> web.Response:
    user = await _current_user(request)
    if user is None:
        return _error(401, "Sign in required")

    body = await _read_json(request)
    if isinstance(body, web.Response):
        return body

    environment = str(body.get("environment") or "live")
    if environment not in ("live", "test"):
        return _error(400, "environment must be 'live' or 'test'")
    scopes = body.get("scopes")
    scopes_tuple = (
        tuple(str(scope) for scope in scopes) if isinstance(scopes, list) else ()
    )

    raw = generate_api_key(environment)
    storage = _services(request).storage
    key = await storage.create_api_key(
        key_hash=hash_api_key(raw),
        key_prefix=key_prefix(raw),
        name=str(body.get("name") or "Untitled key"),
        environment=environment,
        scopes=scopes_tuple,
        user_id=user.id,
    )
    payload = _serialize_key(key)
    payload["secret"] = raw  # returned once, never stored in plain text
    return web.json_response(payload, status=201)


async def revoke_key_endpoint(request: web.Request) -> web.Response:
    user = await _current_user(request)
    if user is None:
        return _error(401, "Sign in required")
    key_id = int(request.match_info["key_id"])
    storage = _services(request).storage
    owned = await storage.list_api_keys(user.id)
    if not any(key.id == key_id for key in owned):
        return _error(404, "Key not found")
    await storage.revoke_api_key(key_id)
    return web.json_response({"ok": True})


async def delete_key_endpoint(request: web.Request) -> web.Response:
    user = await _current_user(request)
    if user is None:
        return _error(401, "Sign in required")
    key_id = int(request.match_info["key_id"])
    await _services(request).storage.delete_api_key(key_id, user.id)
    return web.json_response({"ok": True})


async def usage_endpoint(request: web.Request) -> web.Response:
    user = await _current_user(request)
    if user is None:
        return _error(401, "Sign in required")

    try:
        days = int(request.query.get("days", "14"))
    except ValueError:
        days = 14
    days = max(1, min(days, 90))

    storage = _services(request).storage
    summary = await storage.user_usage_summary(user.id, days=days)
    series = await storage.api_usage_series(user.id, days=days)
    by_model = await storage.api_usage_breakdown(user.id, "model")
    by_endpoint = await storage.api_usage_breakdown(user.id, "endpoint")
    by_symbol = await storage.api_usage_breakdown(user.id, "symbol")
    recent = await storage.recent_api_usage(user.id, limit=8)

    return web.json_response(
        {
            "summary": {
                "total": summary.total,
                "today": summary.today,
                "errors": summary.errors,
                "success_rate": summary.success_rate,
            },
            "series": series,
            "by_model": by_model,
            "by_endpoint": by_endpoint,
            "by_symbol": by_symbol,
            "recent": recent,
        }
    )


# --- API: account settings (session-authenticated) -------------------------

_SETTINGS_FIELDS = {
    "language",
    "currency",
    "timezone",
    "theme",
    "density",
    "default_model",
    "default_symbol",
    "default_timeframe",
    "notifications",
}


def _serialize_settings(settings: Any) -> dict[str, Any]:
    return {
        "language": settings.language,
        "currency": settings.currency,
        "timezone": settings.timezone,
        "theme": settings.theme,
        "density": settings.density,
        "default_model": settings.default_model,
        "default_symbol": settings.default_symbol,
        "default_timeframe": settings.default_timeframe,
        "notifications": settings.notifications,
        "updated_at": settings.updated_at.isoformat()
        if settings.updated_at
        else None,
    }


async def get_settings_endpoint(request: web.Request) -> web.Response:
    user = await _current_user(request)
    if user is None:
        return _error(401, "Sign in required")
    settings = await _services(request).storage.get_user_settings(user.id)
    return web.json_response(_serialize_settings(settings))


async def update_settings_endpoint(request: web.Request) -> web.Response:
    user = await _current_user(request)
    if user is None:
        return _error(401, "Sign in required")

    body = await _read_json(request)
    if isinstance(body, web.Response):
        return body
    changes = {key: value for key, value in body.items() if key in _SETTINGS_FIELDS}
    settings = await _services(request).storage.update_user_settings(
        user.id, **changes
    )
    return web.json_response(_serialize_settings(settings))


async def change_password_endpoint(request: web.Request) -> web.Response:
    user = await _current_user(request)
    if user is None:
        return _error(401, "Sign in required")

    body = await _read_json(request)
    if isinstance(body, web.Response):
        return body

    new_password = str(body.get("new_password") or "")
    if len(new_password) < 8:
        return _error(400, "New password must be at least 8 characters")

    storage = _services(request).storage
    existing = await storage.get_api_user_password_hash(user.id)
    if existing:
        current = str(body.get("current_password") or "")
        if not verify_password(current, existing):
            return _error(400, "Current password is incorrect")

    await storage.set_api_user_password(user.id, hash_password(new_password))
    return web.json_response({"ok": True})


# --- health ----------------------------------------------------------------


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_web_app(application: Any, settings: Settings) -> web.Application:
    """Build the aiohttp application serving Telegram + the v3 API."""
    app = web.Application(
        client_max_size=MAX_BODY_BYTES, middlewares=[cors_middleware]
    )
    app[TELEGRAM_APPLICATION_KEY] = application
    app[SETTINGS_KEY] = settings
    if not settings.api_keys:
        logger.info(
            "PKAY_API_KEYS not set; static keys disabled "
            "(database keys are still accepted)"
        )
    app.router.add_get("/health", health)
    app.router.add_post("/webhook", telegram_webhook)
    app.router.add_post("/api/v3/agents", agents_endpoint)
    app.router.add_post("/api/v3/analyze", analyze_endpoint)
    app.router.add_get("/api/v3/auth/google", google_login)
    app.router.add_get("/api/v3/auth/google/callback", google_callback)
    app.router.add_get("/api/v3/auth/me", auth_me)
    app.router.add_get("/api/v3/keys", keys_endpoint)
    app.router.add_post("/api/v3/keys", create_key_endpoint)
    app.router.add_post("/api/v3/keys/{key_id}/revoke", revoke_key_endpoint)
    app.router.add_delete("/api/v3/keys/{key_id}", delete_key_endpoint)
    app.router.add_get("/api/v3/usage", usage_endpoint)
    app.router.add_get("/api/v3/settings", get_settings_endpoint)
    app.router.add_put("/api/v3/settings", update_settings_endpoint)
    app.router.add_post("/api/v3/auth/password", change_password_endpoint)
    return app
