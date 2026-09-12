"""API key authentication for the public v3 endpoints."""

from __future__ import annotations

import hmac
from collections.abc import Iterable


def extract_bearer(header: str | None) -> str | None:
    """Return the token from an ``Authorization: Bearer <token>`` header."""
    if not header:
        return None
    parts = header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def check_api_key(token: str | None, keys: Iterable[str]) -> bool:
    """Validate ``token`` against the configured API ``keys``.

    When no keys are configured the API is open (local/development). Production
    deployments should always set ``PKAY_API_KEYS``.
    """
    key_list = tuple(key for key in keys if key)
    if not key_list:
        return True
    if not token:
        return False
    return any(hmac.compare_digest(token, key) for key in key_list)
