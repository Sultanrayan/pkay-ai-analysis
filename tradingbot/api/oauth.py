"""Google OAuth 2.0 helpers for the public API.

The flow is authorization-code based:

    GET  /api/v3/auth/google            -> 302 to Google consent
    GET  /api/v3/auth/google/callback   -> exchange code, create the API user,
                                           issue a session token

Session tokens are short HMAC-signed strings (no extra dependency).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Any
from urllib.parse import urlencode

from ..config import Settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPES = "openid email profile"


def new_state() -> str:
    """Random CSRF state value for the authorization request."""
    return secrets.token_urlsafe(24)


def build_authorize_url(settings: Settings, state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
        "include_granted_scopes": "true",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code(settings: Settings, http: Any, code: str) -> dict[str, Any]:
    response = await http.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri,
        },
    )
    response.raise_for_status()
    return response.json()


async def fetch_userinfo(http: Any, access_token: str) -> dict[str, Any]:
    response = await http.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


def _secret(settings: Settings) -> str:
    return (
        settings.session_secret
        or settings.google_client_secret
        or "pkay-dev-session-secret"
    )


def create_session_token(
    settings: Settings, user_id: int, ttl_seconds: int = 60 * 60 * 24 * 30
) -> str:
    expiry = int(time.time()) + ttl_seconds
    payload = f"{user_id}:{expiry}"
    signature = hmac.new(
        _secret(settings).encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    raw = f"{payload}:{signature}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def verify_session_token(settings: Settings, token: str | None) -> int | None:
    if not token:
        return None
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode()).decode()
        user_id_str, expiry_str, signature = raw.split(":", 2)
        payload = f"{user_id_str}:{expiry_str}"
        expected = hmac.new(
            _secret(settings).encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        if int(expiry_str) < int(time.time()):
            return None
        return int(user_id_str)
    except Exception:
        return None
