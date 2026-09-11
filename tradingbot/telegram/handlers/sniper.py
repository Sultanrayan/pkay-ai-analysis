"""/sniper command and the signal-only memecoin scan flow.

The scan is deliberately **detection only**: it ranks opportunities from the
data layer (demo scanner unless a live DEX feed is wired) and displays their
safety profile. No order is ever placed.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ...agents import sniper as sniper_agent
from ..formatter import sniper_html
from ..i18n import I18n
from ..keyboards import main_menu
from ..support import answer_callback, ensure_user, get_services, send_or_edit


async def cmd_sniper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """``/sniper`` — run the scan and show the opportunities page."""
    await run_sniper_scan(update, context)


async def on_sniper(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: tuple[str, ...]) -> None:
    """Callback from the main menu / report-action Sniper button."""
    await run_sniper_scan(update, context)


async def run_sniper_scan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shared scan execution: fetch -> rank -> render."""
    user = await ensure_user(update, context)
    i18n = I18n(user.language)
    services = get_services(context)
    await answer_callback(update)

    scan = await services.data_manager.get_sniper_scan()
    result = sniper_agent.analyze(
        scan,
        min_liquidity=services.settings.sniper_min_liquidity,
        max_opportunities=services.settings.sniper_max_opportunities,
    )
    await send_or_edit(update, context, sniper_html(result, i18n), main_menu(i18n))