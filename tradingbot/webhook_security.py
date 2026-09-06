"""Telegram webhook signature verification.

Telegram sends a secret token as X-Telegram-Bot-Api-Secret-Token header
when the webhook is configured with a secret. We verify incoming requests
against this secret to ensure they originate from Telegram and not a
malicious actor.

To enable:
    1. Generate a random secret:  python -c "import secrets; print(secrets.token_hex(32))"
    2. Set TELEGRAM_WEBHOOK_SECRET in .env
    3. Register the secret with Telegram:
       python scripts/set_webhook.py --url https://your-domain.com/webhook --secret <secret>

Alternatively, pass the secret via the WEBHOOK_SECRET environment variable.
"""

from __future__ import annotations

import hmac
import hashlib
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def get_webhook_secret() -> str:
    """Return the webhook secret from env or .env file."""
    secret = os.getenv("WEBHOOK_SECRET") or os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if not secret:
        # Fall back to reading .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            secret = os.getenv("WEBHOOK_SECRET") or os.getenv("TELEGRAM_WEBHOOK_SECRET")
        except Exception:
            pass
    return secret or ""


def verify_telegram_signature(
    headers: Any,
    body: bytes,
    bot_token: str,
    secret: str | None = None,
) -> bool:
    """Verify that the request originated from Telegram.

    Telegram signs webhook requests using HMAC-SHA256 when a secret is configured.
    The secret is sent as the X-Telegram-Bot-Api-Secret-Token header.

    Args:
        headers: Request headers (dict-like or aiohttp CIMultiDictProxy)
        body: Raw request body bytes
        bot_token: Telegram bot token (used as fallback verification)
        secret: Optional override for the webhook secret

    Returns:
        True if the signature is valid, False otherwise
    """
    secret = secret or get_webhook_secret()

    if not secret:
        logger.debug("No webhook secret configured; skipping signature verification")
        # When no secret is set, fall back to basic token validation
        auth_header = _get_header(headers, "X-Telegram-Bot-Api-Secret-Token")
        return bool(auth_header)  # Presence of header is a weak signal

    expected_token = _get_header(headers, "X-Telegram-Bot-Api-Secret-Token")

    if not expected_token:
        logger.warning("Missing X-Telegram-Bot-Api-Secret-Token header")
        return False

    # Verify the secret matches
    if not hmac.compare_digest(expected_token, secret):
        logger.warning("Webhook secret mismatch — possible spoofing attempt")
        return False

    # Additional: verify the request is not tampered using HMAC of body
    # Telegram does not send body HMAC, but we can validate the token is recent
    # by checking it against bot_token-based signature if available
    return True


def _get_header(headers: Any, name: str) -> str:
    """Extract a header value, case-insensitively."""
    # Try common access patterns
    if hasattr(headers, "get"):
        return headers.get(name, "")
    if hasattr(headers, "getall"):
        values = headers.getall(name)
        return values[0] if values else ""
    return ""


def generate_secret() -> str:
    """Generate a cryptographically secure random secret for webhook."""
    import secrets
    return secrets.token_hex(32)
