"""Standalone public JSON API server (no Telegram).

Usage:
    python api_server.py

Serves the same endpoints as the bot's combined server, but without the
Telegram webhook and without requiring ``TELEGRAM_BOT_TOKEN``:

* ``POST /api/v3/analyze`` — multi-agent analysis (built-in AI analysis)
* ``POST /api/v3/agents``  — AI Agent Team functions (functions-only)
* ``GET  /health``
"""

from __future__ import annotations

import asyncio
import signal
from types import SimpleNamespace

from aiohttp import web

from tradingbot.api.server import create_web_app
from tradingbot.config import Settings, setup_logging
from tradingbot.services import build_services, close_services


async def _serve(settings: Settings) -> None:
    services = await build_services(settings)
    application = SimpleNamespace(bot_data={"services": services})

    app = create_web_app(application, settings)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.webhook_host, settings.webhook_port)
    await site.start()
    print(
        f"Pkay AI API listening on {settings.webhook_host}:{settings.webhook_port}"
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except (NotImplementedError, RuntimeError):
            pass

    try:
        await stop.wait()
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()
        await close_services(services)


def main() -> None:
    settings = Settings.from_env()
    setup_logging(settings.log_level)
    try:
        asyncio.run(_serve(settings))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
