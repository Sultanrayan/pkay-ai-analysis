"""Shared Telegram :class:`Application` assembly.

Both entry points (``bot.py`` polling, ``webhook_server.py`` webhook) build
their runtime through :func:`build_application` so wiring, startup and
shutdown behaviour live in exactly one place.
"""

from __future__ import annotations

import logging

from telegram.ext import Application

from .config import Settings
from .services import build_services, close_services
from .telegram.handlers import register_handlers

logger = logging.getLogger(__name__)


async def _post_init(application: Application) -> None:
    """Create the runtime service bag once the event loop is available."""
    settings: Settings = application.bot_data["settings"]
    application.bot_data["services"] = await build_services(settings)
    logger.info(
        "Services ready (storage=%s, data=%s)",
        type(application.bot_data["services"].storage).__name__,
        "demo" if settings.use_demo_data else "live+demo-fallback",
    )


async def _post_shutdown(application: Application) -> None:
    """Release connections (HTTP, Redis, PostgreSQL pools)."""
    services = application.bot_data.get("services")
    if services is not None:
        await close_services(services)


def build_application(settings: Settings) -> Application:
    """Build a configured bot application ready to poll or run a webhook."""
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )
    application.bot_data["settings"] = settings
    register_handlers(application)
    return application
