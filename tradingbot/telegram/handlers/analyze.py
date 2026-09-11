"""/analyze command and the asset -> timeframe -> run -> report flow."""

from __future__ import annotations

import logging

from telegram import InputFile, Message, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from ...domain import Symbol, Timeframe
from ...exporter import history_row_to_csv
from ...storage.models import history_row_from_report
from .. import callback_data as cb
from ..formatter import report_html, split_message
from ..i18n import I18n
from ..keyboards import asset_picker, report_actions, timeframe_picker
from ..support import answer_callback, ensure_user, get_services, send_or_edit

logger = logging.getLogger(__name__)

#: Special token representing "run all assets" in callback payloads.
ALL = "ALL"
#: Special token in the asset picker that jumps straight to the sniper scan.
MEMECOIN = "MEMECOIN"

LAST_REQUEST_KEY = "last_request"  # user_data -> {symbol, timeframe, row_id}

TIMEFRAME_DISPLAY = {
    Timeframe.H1: "1H",
    Timeframe.H4: "4H",
    Timeframe.D1: "1D",
    Timeframe.W1: "1W",
}


# --------------------------------------------------------------------------
# /analyze command
# --------------------------------------------------------------------------

async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parse ``/analyze [symbol] [timeframe]`` or start the button flow."""
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    services = get_services(context)
    prefs = await services.storage.get_preferences(user.user_id)

    symbols: list[Symbol] | None = None
    timeframe: Timeframe | None = None
    for token in context.args or []:
        lowered = token.lower()
        if lowered in ("both", "all"):
            symbols = list(Symbol)
        elif timeframe is None and Timeframe.parse(token):
            timeframe = Timeframe.parse(token)
        elif symbols is None and (parsed := Symbol.parse(token)):
            symbols = [parsed]
    timeframe = timeframe or prefs.default_timeframe or services.settings.default_timeframe

    if symbols is None:
        # No symbol given: open the asset picker.
        await answer_callback(update)
        await send_or_edit(update, context, i18n.t("asset_prompt"), asset_picker(i18n))
        return

    for index, symbol in enumerate(symbols):
        await _perform_analysis(update, context, symbol, timeframe, force_new=index > 0)


# --------------------------------------------------------------------------
# Callback flow: asset -> timeframe -> run
# --------------------------------------------------------------------------

async def on_asset(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    """Show the timeframe picker once an asset (or all) is selected; the
    memecoin button jumps straight to the signal-only sniper scan."""
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    await answer_callback(update)

    token = parts[1].upper() if len(parts) >= 2 else ""
    if token == MEMECOIN:
        from .sniper import run_sniper_scan

        await run_sniper_scan(update, context)
        return
    if token == ALL:
        label = i18n.t("btn_all")
    elif Symbol.parse(token):
        label = token
    else:
        await send_or_edit(update, context, i18n.t("asset_prompt"), asset_picker(i18n))
        return
    await send_or_edit(update, context, i18n.t("tf_prompt", symbol=label), timeframe_picker(token, i18n))


async def on_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    """Run analysis for the chosen asset(s) and timeframe."""
    if len(parts) < 3:
        await answer_callback(update)
        return
    timeframe = Timeframe.parse(parts[2])
    symbols = _symbols_for_token(parts[1])
    if not symbols or timeframe is None:
        await answer_callback(update)
        return
    await answer_callback(update)
    for index, symbol in enumerate(symbols):
        await _perform_analysis(update, context, symbol, timeframe, force_new=index > 0)


async def on_run(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    """Run an analysis encoded directly in the callback (run:SYMBOL:TF)."""
    if len(parts) < 3:
        await answer_callback(update)
        return
    timeframe = Timeframe.parse(parts[2])
    symbols = _symbols_for_token(parts[1])
    if not symbols or timeframe is None:
        await answer_callback(update)
        return
    await answer_callback(update)
    for index, symbol in enumerate(symbols):
        await _perform_analysis(update, context, symbol, timeframe, force_new=index > 0)


def _symbols_for_token(token: str) -> list[Symbol]:
    """Resolve a callback token (BTCUSDT/.../XAUUSD/ALL) to concrete symbols."""
    if token.upper() == ALL:
        return list(Symbol)
    symbol = Symbol.parse(token)
    return [symbol] if symbol else []


# --------------------------------------------------------------------------
# Report action buttons (under a delivered report)
# --------------------------------------------------------------------------

async def on_report_action(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    """Handle report:refresh / report:export / report:history / report:menu."""
    if len(parts) < 2:
        await answer_callback(update)
        return
    action = parts[1]
    if action == cb.REPORT_REFRESH:
        await _refresh_last(update, context)
    elif action == cb.REPORT_EXPORT:
        await _export_last(update, context)
    elif action == cb.REPORT_HISTORY:
        from .navigation import on_history

        await on_history(update, context, (cb.HISTORY,))
    elif action == cb.REPORT_MENU:
        from .navigation import on_menu

        await on_menu(update, context, (cb.MENU,))


async def _refresh_last(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Re-run the most recent analysis (same symbol/timeframe)."""
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    last = context.user_data.get(LAST_REQUEST_KEY)
    if not last:
        await send_or_edit(update, context, i18n.t("error_generic"))
        return
    symbol = Symbol.parse(str(last["symbol"]))
    timeframe = Timeframe.parse(str(last["timeframe"]))
    if symbol is None or timeframe is None:
        await send_or_edit(update, context, i18n.t("error_generic"))
        return
    await _perform_analysis(update, context, symbol, timeframe)


async def _export_last(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the most recent analysis row as a CSV document."""
    user = await ensure_user(update, context)
    services = get_services(context)
    i18n = I18n(user.language)
    last = context.user_data.get(LAST_REQUEST_KEY)
    row_id = last.get("row_id") if last else None
    if row_id is None:
        await answer_callback(update, i18n.t("error_generic"))
        return
    row = await services.storage.get_history_row(user.user_id, int(row_id))
    if row is None:
        await answer_callback(update, i18n.t("error_generic"))
        return
    filename = f"analysis_{row.symbol}_{row.timeframe}_{row.id}.csv"
    document = InputFile(history_row_to_csv(row).encode("utf-8"), filename=filename)
    chat = update.effective_chat
    if chat is not None:
        await context.bot.send_document(chat_id=chat.id, document=document)
    await answer_callback(update, i18n.t("exported"))


# --------------------------------------------------------------------------
# Shared analysis execution
# --------------------------------------------------------------------------

async def _perform_analysis(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    symbol: Symbol,
    timeframe: Timeframe,
    *,
    force_new: bool = False,
) -> Message | None:
    """Run one analysis and render the report into the conversation."""
    services = get_services(context)
    user = await ensure_user(update, context)
    i18n = I18n(user.language)

    # Consume a daily request *before* doing any work (fixed window in Redis).
    status = await services.limiter.consume(user.user_id, services.settings.max_daily_requests)
    if not status.allowed:
        await answer_callback(update)
        text = i18n.t("rate_limited", limit=status.limit)
        return await send_or_edit(update, context, text, force_new=force_new)

    placeholder = await send_or_edit(
        update,
        context,
        i18n.t("analyzing", symbol=symbol.value, timeframe=TIMEFRAME_DISPLAY[timeframe]),
        force_new=force_new,
    )
    chat_id = update.effective_chat.id if update.effective_chat else None
    message_id = placeholder.message_id if placeholder else None

    try:
        report = await services.runner.analyze(symbol, timeframe)
    except ValueError as exc:
        logger.warning("Analysis rejected input for %s %s: %s", symbol.value, timeframe.value, exc)
        return await _edit_or_send(chat_id, message_id, context, i18n.t("error_generic"), None)
    except Exception:
        logger.exception("Analysis failed for %s %s", symbol.value, timeframe.value)
        return await _edit_or_send(chat_id, message_id, context, i18n.t("error_generic"), None)

    # Persist a history row so /history and Export have something to read.
    prefs = await services.storage.get_preferences(user.user_id)
    row = history_row_from_report(report, user.user_id)
    row.chart_url = _render_chart_image(report, services, i18n)
    row_id = await services.storage.add_analysis(row)
    await services.storage.register_analysis_request(user.user_id)
    context.user_data[LAST_REQUEST_KEY] = {
        "symbol": symbol.value,
        "timeframe": timeframe.value,
        "row_id": row_id,
    }

    # Render the report (HTML), splitting very long text over several messages.
    keyboard = report_actions(i18n)
    chunks = split_message(report_html(report, i18n, prefs))
    final_message = await _edit_or_send(chat_id, message_id, context, chunks[0], None)
    if len(chunks) > 1:
        for extra in chunks[1:-1]:
            final_message = await context.bot.send_message(
                chat_id=chat_id,
                text=extra,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        final_message = await context.bot.send_message(
            chat_id=chat_id,
            text=chunks[-1],
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    # Attach the optional candlestick chart image.
    if row.chart_url and chat_id is not None:
        chart_path = services.settings.chart_path / row.chart_url
        if chart_path.exists():
            try:
                caption = f"📊 <b>{symbol.value} {TIMEFRAME_DISPLAY[timeframe]}</b>"
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=InputFile(chart_path.read_bytes(), filename=chart_path.name),
                    caption=caption,
                    parse_mode="HTML",
                )
            except TelegramError:
                logger.warning("Failed to attach chart for %s", symbol.value, exc_info=True)

    if final_message is not None:
        await services.storage.set_analysis_message_id(row_id, final_message.message_id)
    return final_message


def _render_chart_image(report, services, i18n: I18n) -> str | None:
    """Render the report's candles to PNG; returns the filename or None.

    Chart failures are never fatal — the text report always goes through.
    """
    if not (services.settings.chart_enabled and report.candles):
        return None
    try:
        from ...charts import render_chart
        from ...indicators import sma_series

        closes = [c.close for c in report.candles]
        overlays = [sma_series(closes, 50), sma_series(closes, 200)]
        name = f"{report.symbol.value}_{report.timeframe.value}_{report.created_at:%Y%m%d_%H%M%S}.png"
        output = services.settings.chart_path / name
        render_chart(
            report.candles,
            output,
            title=f"{report.symbol.value} {TIMEFRAME_DISPLAY[report.timeframe]}",
            ma_series=overlays,
        )
        return name
    except Exception:
        logger.warning("Chart rendering failed", exc_info=True)
        return None


async def _edit_or_send(
    chat_id: int | None,
    message_id: int | None,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup,
) -> Message | None:
    """Edit the placeholder message or send a fresh one as a fallback."""
    if chat_id is not None and message_id is not None:
        try:
            return await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except TelegramError:
            logger.info("Could not edit message %s; sending a new one", message_id)
    if chat_id is None:
        return None
    return await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
