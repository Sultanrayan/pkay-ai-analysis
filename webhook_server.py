"""Production entry point: run the bot behind a Telegram webhook.

Usage:
    python webhook_server.py

Requires TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_URL (public HTTPS) in .env.
The application registers the webhook with Telegram on startup and serves
``POST /webhook`` on WEBHOOK_HOST:WEBHOOK_PORT.
"""

from __future__ import annotations

import sys

from telegram import Update

from tradingbot.application import build_application
from tradingbot.config import Settings, setup_logging

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
        sys.exit(
            "TELEGRAM_WEBHOOK_URL is empty. Set it to your public HTTPS URL "
            "(e.g. https://bot.example.com/webhook) in .env."
        )

    application = build_application(settings)
    print(
        f"Bot started in webhook mode: {settings.telegram_webhook_url} "
        f"listening on {settings.webhook_host}:{settings.webhook_port}{URL_PATH}"
    )
    application.run_webhook(
        listen=settings.webhook_host,
        port=settings.webhook_port,
        url_path=URL_PATH,
        webhook_url=settings.telegram_webhook_url,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
