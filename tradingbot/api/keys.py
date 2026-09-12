"""Public API key helpers.

Keys are shown once (``pk_live_...``) and only their SHA-256 hash is stored,
so a database leak does not expose usable keys.
"""

from __future__ import annotations

import hashlib
import secrets
import string

_ALPHABET = string.ascii_letters + string.digits


def generate_api_key(environment: str = "live") -> str:
    """Return a new raw API key, e.g. ``pk_live_ab12...``."""
    token = "".join(secrets.choice(_ALPHABET) for _ in range(32))
    return f"pk_{environment}_{token}"


def hash_api_key(key: str) -> str:
    """Return the stable SHA-256 hex digest used as the lookup hash."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def key_prefix(key: str) -> str:
    """Return a safe display prefix (never enough to reconstruct the key)."""
    return key[:12]
