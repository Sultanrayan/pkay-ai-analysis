"""Production entry point: run the bot behind a Telegram webhook.

Usage:
    python webhook_server.py

Requires TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_URL (public HTTPS) in .env.
The application registers the webhook with Telegram on startup and serves
``POST /webhook`` on WEBHOOK_HOST:WEBHOOK_PORT.

Railway deployment:
    - Set WEBHOOK_HOST=0.0.0.0
    - Set WEBHOOK_PORT from Railway's PORT env var (default 8080)
    - Router must expose POST /webhook
"""

from __future__ import annotations

import sys
import os

from telegram import Update

from tradingbot.application import build_application
from tradingbot.config import Settings, setup_logging
from tradingbot.webhook_security import verify_telegram_signature, get_webhook_secret

URL_PATH = "/webhook"


def main() -> None:
    settings = Settings.from_env()
    setup_logging(settings.log_level)

    if not settings.telegram_bot_token or settings.telegram_bot_token.startswith("your_"):
        sys.exit(
            "No TELEGRAM_BOT_TOKEN configured. Copy .env.example to .env and "
            "add your token from @BotFather."
        )
    if not settings.telegram_webhook_url:
        # Auto-detect Railway domain if available
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if railway_domain:
            settings = Settings(
                **{k: v for k, v in settings.__dict__.items() if k != "telegram_webhook_url"},
                telegram_webhook_url=f"https://{railway_domain}/webhook",
            )
            print(f"Auto-configured TELEGRAM_WEBHOOK_URL: https://{railway_domain}/webhook")
        else:
            sys.exit(
                "TELEGRAM_WEBHOOK_URL is empty. Set it to your public HTTPS URL "
                "(e.g. https://bot.example.com/webhook) in .env."
            )

    # Warn if webhook secret is not configured
    webhook_secret = get_webhook_secret()
    if not webhook_secret:
        print(
            "WARNING: TELEGRAM_WEBHOOK_SECRET is not set. "
            "For production, generate a secret and set it via:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\"\n"
            "Then set WEBHOOK_SECRET in your environment."
        )

    application = build_application(settings)
    print(
        f"Bot started in webhook mode: {settings.telegram_webhook_url} "
        f"listening on {settings.webhook_host}:{settings.webhook_port}{URL_PATH}"
    )

    # Wrap the webhook handler with signature verification
    async def secured_webhook_handler(request, update, context):
        """Verify Telegram signature before processing the update."""
        if not verify_telegram_signature(
            request.headers,
            request.content.read(),
            settings.telegram_bot_token,
            webhook_secret,
        ):
            logging.getLogger(__name__).warning(
                "Invalid Telegram webhook signature — request rejected"
            )
            return
        # Re-read content for the update dispatcher
        request._content = request.content._buffer
        return await application.process_update(update, context)

    application.run_webhook(
        listen=settings.webhook_host,
        port=settings.webhook_port,
        url_path=URL_PATH,
        webhook_url=settings.telegram_webhook_url,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
