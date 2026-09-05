"""Slash-command handlers: /start, /help, /about, /cancel and free-text."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ... import __version__ as bot_version
from ..formatter import about_html, help_html, welcome_html
from ..i18n import I18n
from ..keyboards import main_menu
from ..support import answer_callback, ensure_user, get_services, send_or_edit


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    text = welcome_html(i18n, user.first_name)
    await send_or_edit(update, context, text, main_menu(i18n))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    limit = get_services(context).settings.max_daily_requests
    await send_or_edit(update, context, help_html(i18n, limit), main_menu(i18n))


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    await send_or_edit(update, context, about_html(i18n, bot_version), main_menu(i18n))


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await ensure_user(update, context)
    context.user_data.pop("last_request", None)
    i18n = I18n(user.language)
    await answer_callback(update)
    await send_or_edit(update, context, i18n.t("cancel_done"), main_menu(i18n))


async def on_unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Politely route unrecognised free text back to the command menu."""
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    await answer_callback(update)
    limit = get_services(context).settings.max_daily_requests
    await send_or_edit(update, context, help_html(i18n, limit), main_menu(i18n))
