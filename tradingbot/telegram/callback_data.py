"""Inline callback-data conventions.

Callback payloads are colon-separated tokens, e.g. ``run:BTCUSDT:1h``, so the
router can split on the first token and every button carries just enough
context to act on itself (no fragile session ordering).

First-token vocabulary:
    menu            -> show the main menu
    help            -> show help text
    asset           -> open the asset picker (asset:PICK or asset)
    tf              -> choose a timeframe for an asset (tf:SYMBOL)
    run             -> execute an analysis (run:SYMBOL:TIMEFRAME)
    report          -> action on the last report (report:refresh|export|history|menu)
    history         -> list history (history or history:ROW_ID)
    settings        -> open settings panel (settings)
    lang            -> set language (lang:en|kh)
    toggle          -> flip a boolean preference (toggle:show_chart|...)
"""

from __future__ import annotations

from ..domain import Symbol, Timeframe

MENU = "menu"
HELP = "help"
HISTORY = "history"
SETTINGS = "settings"

PREFIX_ASSET = "asset"
PREFIX_TIMEFRAME = "tf"
PREFIX_RUN = "run"
PREFIX_REPORT = "report"
PREFIX_SNIPER = "sniper"
PREFIX_LANG = "lang"
PREFIX_TOGGLE = "toggle"

# Report action tokens (after the report: prefix).
REPORT_REFRESH = "refresh"
REPORT_EXPORT = "export"
REPORT_HISTORY = "history"
REPORT_MENU = "menu"


def asset_picker() -> str:
    return PREFIX_ASSET


def pick_asset(symbol: Symbol) -> str:
    return f"{PREFIX_ASSET}:{symbol.value}"


def pick_timeframe(symbol_token: str, timeframe: Timeframe) -> str:
    """Callback for choosing a timeframe; token may be a Symbol value or BOTH."""
    return f"{PREFIX_TIMEFRAME}:{symbol_token}:{timeframe.value}"


def run(symbol: Symbol, timeframe: Timeframe) -> str:
    return f"{PREFIX_RUN}:{symbol.value}:{timeframe.value}"


def report(action: str) -> str:
    return f"{PREFIX_REPORT}:{action}"


def sniper_scan() -> str:
    return PREFIX_SNIPER


def history_list() -> str:
    return HISTORY


def history_open(row_id: int) -> str:
    return f"{HISTORY}:{row_id}"


def set_language(code: str) -> str:
    return f"{PREFIX_LANG}:{code}"


def toggle(field: str) -> str:
    return f"{PREFIX_TOGGLE}:{field}"


def parse(data: str | None) -> tuple[str, ...]:
    """Split a callback payload into its tokens (empty -> ())."""
    if not data:
        return ()
    return tuple(part for part in data.split(":") if part)


def symbol_from(token: str) -> Symbol | None:
    return Symbol.parse(token)


def timeframe_from(token: str) -> Timeframe | None:
    return Timeframe.parse(token)
