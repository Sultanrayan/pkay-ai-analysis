"""Production entry point: Telegram webhook + public JSON API (v3).

Usage:
    python webhook_server.py

A single aiohttp server (WEBHOOK_HOST:WEBHOOK_PORT) exposes:

* ``POST /webhook``          — Telegram updates
* ``POST /api/v3/analyze``   — multi-agent analysis for a Data Pair
* ``POST /api/v3/agents``    — AI Agent Team functions (functions-only)
* ``GET  /health``           — liveness probe

Requires TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_URL (public HTTPS) in .env.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys

from aiohttp import web
from telegram import Update

from tradingbot.api.server import create_web_app
from tradingbot.application import build_application
from tradingbot.config import Settings, setup_logging
from tradingbot.webhook_security import get_webhook_secret

URL_PATH = "/webhook"


async def _serve(settings: Settings, webhook_secret: str) -> None:
    application = build_application(settings, with_updater=False)
    await application.initialize()  # runs post_init -> builds services
    await application.start()

    await application.bot.set_webhook(
        url=settings.telegram_webhook_url,
        secret_token=webhook_secret or None,
        allowed_updates=Update.ALL_TYPES,
    )

    app = create_web_app(application, settings)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.webhook_host, settings.webhook_port)
    await site.start()

    print(
        "Serving Telegram webhook + v3 API on "
        f"{settings.webhook_host}:{settings.webhook_port} "
        f"(webhook: {settings.telegram_webhook_url})"
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except (NotImplementedError, RuntimeError):
            pass  # Windows / non-main thread: rely on KeyboardInterrupt

    try:
        await stop.wait()
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()
        await application.stop()
        await application.shutdown()


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
                telegram_webhook_url=f"https://{railway_domain}{URL_PATH}",
            )
            print(f"Auto-configured TELEGRAM_WEBHOOK_URL: https://{railway_domain}{URL_PATH}")
        else:
            sys.exit(
                "TELEGRAM_WEBHOOK_URL is empty. Set it to your public HTTPS URL "
                "(e.g. https://bot.example.com/webhook) in .env."
            )

    webhook_secret = get_webhook_secret()
    if not webhook_secret:
        print(
            "WARNING: WEBHOOK_SECRET is not set. For production, generate a secret "
            "and set it via:\n"
            '  python -c "import secrets; print(secrets.token_hex(32))"'
        )
    if not settings.api_keys:
        print(
            "WARNING: PKAY_API_KEYS is not set; the v3 API is open. "
            "Set comma-separated keys to require Bearer auth."
        )

    try:
        asyncio.run(_serve(settings, webhook_secret))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
