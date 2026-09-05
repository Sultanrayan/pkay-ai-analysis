"""Small shared helpers for Telegram handlers.

Keeps repetitive plumbing (services lookup, user registration, message
send-or-edit, HTML mode) in one place so the actual handlers read like
business logic.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telegram import InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes

from ..storage.models import TelegramUser

if TYPE_CHECKING:
    from ..services import Services

logger = logging.getLogger(__name__)

HTML = ParseMode.HTML


def get_services(context: ContextTypes.DEFAULT_TYPE) -> Services:
    """Fetch the runtime service bag installed at startup."""
    return context.bot_data["services"]


async def ensure_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> TelegramUser:
    """Create/refresh the Telegram user row and return it (source of truth
    for the user's language and preferences)."""
    services = get_services(context)
    telegram_user = update.effective_user
    if telegram_user is None:
        raise RuntimeError("Update has no effective user")
    return await services.storage.get_or_create_user(
        telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
        language_code=telegram_user.language_code or "en",
    )


async def answer_callback(update: Update, text: str | None = None) -> None:
    """Acknowledge a callback query so Telegram stops the spinner."""
    query = update.callback_query
    if query is not None:
        try:
            await query.answer(text)
        except TelegramError:
            logger.debug("Callback answer failed", exc_info=True)


async def send_or_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    *,
    force_new: bool = False,
) -> Message | None:
    """Edit the current callback message, or send a new one for commands.

    Falls back to sending a fresh message when the edit fails (e.g. the
    message was deleted). Returns the final message when available. Pass
    ``force_new=True`` to always send a new message (used when one callback
    produces several reports, e.g. "analyze both").
    """
    query = update.callback_query
    chat = update.effective_chat
    if query is not None and not force_new:
        try:
            return await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as exc:
            # Message content unchanged is fine; anything else -> resend.
            if "not modified" not in str(exc).lower():
                logger.info("Edit failed (%s); sending a fresh message", exc)
        except TelegramError as exc:
            logger.info("Edit failed (%s); sending a fresh message", exc)
    if chat is None:
        return None
    try:
        return await context.bot.send_message(
            chat.id,
            text,
            reply_markup=reply_markup,
            parse_mode=HTML,
            disable_web_page_preview=True,
        )
    except TelegramError:
        logger.exception("Failed to send message")
        return None
