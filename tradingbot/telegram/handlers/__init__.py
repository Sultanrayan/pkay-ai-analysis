"""Telegram handlers, grouped by function.

* :mod:`.commands`   — /start, /help, /about, /cancel and text fallbacks
* :mod:`.analyze`    — /analyze plus the asset/timeframe/run/report flow
* :mod:`.sniper`     — /sniper signal-only memecoin scan
* :mod:`.navigation` — menu, history, settings, language and toggles

:func:`register_handlers` wires every handler onto the :class:`Application`;
all callback buttons converge on one router keyed by their first token (see
:mod:`tradingbot.telegram.callback_data`).
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .. import callback_data as cb
from ..i18n import I18n
from ..support import answer_callback, ensure_user, send_or_edit
from . import analyze, commands, navigation, sniper

logger = logging.getLogger(__name__)

#: First callback token -> handler(update, context, parts).
CALLBACK_ROUTER: dict[str, object] = {}


async def _on_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    parts = cb.parse(query.data)
    if not parts:
        await answer_callback(update)
        return
    handler = CALLBACK_ROUTER.get(parts[0])
    if handler is None:
        logger.warning("Unhandled callback data: %r", query.data)
        await answer_callback(update)
        return
    try:
        await handler(update, context, parts)  # type: ignore[misc]
    except Exception:
        logger.exception("Callback handler crashed for data %r", query.data)
        await answer_callback(update)
        user = await ensure_user(update, context)
        i18n = I18n(user.language)
        await send_or_edit(update, context, i18n.t("error_generic"))


def register_handlers(app: Application) -> None:
    """Attach command, message and callback handlers to ``app``."""
    app.add_handler(CommandHandler("start", commands.cmd_start))
    app.add_handler(CommandHandler("help", commands.cmd_help))
    app.add_handler(CommandHandler("about", commands.cmd_about))
    app.add_handler(CommandHandler("cancel", commands.cmd_cancel))
    app.add_handler(CommandHandler("analyze", analyze.cmd_analyze))
    app.add_handler(CommandHandler("sniper", sniper.cmd_sniper))
    app.add_handler(CallbackQueryHandler(_on_callback_query))

    def register(name: str, handler) -> None:
        CALLBACK_ROUTER[name] = handler

    register(cb.MENU, navigation.on_menu)
    register(cb.HELP, navigation.on_help)
    register(cb.HISTORY, navigation.on_history)
    register(cb.SETTINGS, navigation.on_settings)
    register(cb.PREFIX_ASSET, analyze.on_asset)
    register(cb.PREFIX_TIMEFRAME, analyze.on_timeframe)
    register(cb.PREFIX_RUN, analyze.on_run)
    register(cb.PREFIX_REPORT, analyze.on_report_action)
    register(cb.PREFIX_SNIPER, sniper.on_sniper)
    register(cb.PREFIX_LANG, navigation.on_language)
    register(cb.PREFIX_TOGGLE, navigation.on_toggle)

    # Friendly reply to unrecognised free text.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, commands.on_unknown_text))
