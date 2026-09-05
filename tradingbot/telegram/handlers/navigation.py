"""Menu / history / settings / language navigation handlers."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ..formatter import history_detail_html, history_list_html, settings_html, welcome_html
from ..i18n import I18n
from ..keyboards import (
    history_back_actions,
    history_list,
    main_menu,
    settings_panel,
)
from ..support import answer_callback, ensure_user, get_services, send_or_edit

HISTORY_LIMIT = 10


async def on_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    """Show the welcome screen + main menu."""
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    await answer_callback(update)
    await send_or_edit(update, context, welcome_html(i18n, user.first_name), main_menu(i18n))


async def on_help(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    limit = get_services(context).settings.max_daily_requests
    await answer_callback(update)
    text = (
        f"<b>{i18n.t('help_title')}</b>\n\n"
        f"{i18n.t('help_body', limit=limit)}"
    )
    await send_or_edit(update, context, text, main_menu(i18n))


# --------------------------------------------------------------------------
# History
# --------------------------------------------------------------------------

async def on_history(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    """List recent analyses, or open one when a row id is supplied."""
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    services = get_services(context)
    await answer_callback(update)

    if len(parts) >= 2 and parts[1].isdigit():
        row = await services.storage.get_history_row(user.user_id, int(parts[1]))
        if row is None:
            await send_or_edit(update, context, i18n.t("history_empty"), main_menu(i18n))
            return
        await send_or_edit(
            update,
            context,
            history_detail_html(row, i18n),
            history_back_actions(i18n),
        )
        return

    rows = await services.storage.list_history(user.user_id, limit=HISTORY_LIMIT)
    text = history_list_html(rows, i18n, HISTORY_LIMIT)
    keyboard = history_list(rows, i18n) if rows else main_menu(i18n)
    await send_or_edit(update, context, text, keyboard)


# --------------------------------------------------------------------------
# Settings / language / toggles
# --------------------------------------------------------------------------

async def on_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    user = await ensure_user(update, context)
    services = get_services(context)
    prefs = await services.storage.get_preferences(user.user_id)
    i18n = I18n(user.language)
    await answer_callback(update)
    await _show_settings(update, context, prefs, i18n)


async def on_language(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    """Switch the user's language (parts[1] in {en, kh})."""
    user = await ensure_user(update, context)
    if len(parts) < 2 or parts[1] not in ("en", "kh"):
        await answer_callback(update)
        return
    services = get_services(context)
    await services.storage.set_language(user.user_id, parts[1])
    # Re-read so the updated preference is reflected in the panel.
    updated = await services.storage.get_or_create_user(user.user_id)
    prefs = await services.storage.get_preferences(user.user_id)
    await answer_callback(update)
    await _show_settings(update, context, prefs, I18n(updated.language))


async def on_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    """Flip a boolean report preference (parts[1] = field name)."""
    user = await ensure_user(update, context)
    services = get_services(context)
    field = parts[1] if len(parts) >= 2 else ""
    allowed = {"show_chart", "show_indicators", "show_risk", "show_sentiment"}
    if field not in allowed:
        await answer_callback(update)
        return
    prefs = await services.storage.get_preferences(user.user_id)
    current = bool(getattr(prefs, field))
    prefs = await services.storage.update_preferences(user.user_id, **{field: not current})
    i18n = I18n(user.language)
    await answer_callback(update)
    await _show_settings(update, context, prefs, i18n)


async def _show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, prefs, i18n: I18n) -> None:
    """Render the settings panel with its toggle buttons."""
    await send_or_edit(update, context, settings_html(prefs, i18n), settings_panel(prefs, i18n))
