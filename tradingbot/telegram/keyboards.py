"""Inline keyboard builders.

Every builder returns an :class:`InlineKeyboardMarkup` and takes the strings
it should display (from :class:`~.i18n.I18n`) so layout and wording stay
independent.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..domain import Symbol, Timeframe
from ..storage.models import HistoryRow, UserPreferences
from . import callback_data as cb
from .i18n import I18n


def _button(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=data)


def main_menu(i18n: I18n) -> InlineKeyboardMarkup:
    """Welcome menu: one tall button per action."""
    return InlineKeyboardMarkup([
        [_button(i18n.t("btn_analyze"), cb.asset_picker())],
        [_button(i18n.t("btn_history"), cb.history_list())],
        [_button(i18n.t("btn_settings"), cb.SETTINGS)],
        [_button(i18n.t("btn_help"), cb.HELP)],
    ])


def back_row(i18n: I18n) -> list[list[InlineKeyboardButton]]:
    return [[_button(i18n.t("btn_menu"), cb.MENU)]]


def asset_picker(i18n: I18n) -> InlineKeyboardMarkup:
    buttons = [
        [_button(i18n.t("btn_btcusd"), cb.pick_asset(Symbol.BTCUSD))],
        [_button(i18n.t("btn_xauusd"), cb.pick_asset(Symbol.XAUUSD))],
        [_button(i18n.t("btn_both"), cb.asset_picker() + ":both")],
        [_button(i18n.t("btn_menu"), cb.MENU)],
    ]
    return InlineKeyboardMarkup(buttons)


def timeframe_picker(symbol_token: str, i18n: I18n) -> InlineKeyboardMarkup:
    """Timeframe grid for a symbol token (BTCUSD / XAUUSD / BOTH)."""
    buttons: list[list[InlineKeyboardButton]] = [
        [
            _button(i18n.t("tf_1h"), cb.pick_timeframe(symbol_token, Timeframe.H1)),
            _button(i18n.t("tf_4h"), cb.pick_timeframe(symbol_token, Timeframe.H4)),
        ],
        [
            _button(i18n.t("tf_1d"), cb.pick_timeframe(symbol_token, Timeframe.D1)),
            _button(i18n.t("tf_1w"), cb.pick_timeframe(symbol_token, Timeframe.W1)),
        ],
    ]
    buttons.extend(back_row(i18n))
    return InlineKeyboardMarkup(buttons)


def report_actions(i18n: I18n) -> InlineKeyboardMarkup:
    """Action row under a fresh analysis report."""
    buttons = [
        [
            _button(i18n.t("btn_refresh"), cb.report(cb.REPORT_REFRESH)),
            _button(i18n.t("btn_export"), cb.report(cb.REPORT_EXPORT)),
        ],
        [
            _button(i18n.t("btn_history"), cb.report(cb.REPORT_HISTORY)),
            _button(i18n.t("btn_menu"), cb.MENU),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def history_list(rows: list[HistoryRow], i18n: I18n) -> InlineKeyboardMarkup:
    """One button per stored analysis, plus a way back to the menu."""
    buttons: list[list[InlineKeyboardButton]] = [
        [_button(i18n.t("history_row").format(
            row_id=row.id,
            symbol=row.symbol,
            timeframe=row.timeframe,
            signal=row.signal or "—",
        ), cb.history_open(int(row.id)))]
        for row in rows
        if row.id is not None
    ]
    buttons.extend(back_row(i18n))
    return InlineKeyboardMarkup(buttons)


def settings_panel(prefs: UserPreferences, i18n: I18n) -> InlineKeyboardMarkup:
    """Settings rows: language + boolean report toggles, labelled with state."""
    other = "en" if i18n.is_khmer else "kh"
    language_label = i18n.t("settings_lang")
    target_label = i18n.t("lang_en") if other == "en" else i18n.t("lang_kh")

    buttons: list[list[InlineKeyboardButton]] = [
        [_button(f"{language_label}: {target_label}", cb.set_language(other))],
    ]
    toggles = [
        ("show_chart", "settings_chart", prefs.show_chart),
        ("show_indicators", "settings_indicators", prefs.show_indicators),
        ("show_risk", "settings_risk", prefs.show_risk),
        ("show_sentiment", "settings_sentiment", prefs.show_sentiment),
    ]
    for field, label_key, enabled in toggles:
        label = i18n.t(label_key)
        state = i18n.t("value_on") if enabled else i18n.t("value_off")
        buttons.append([_button(f"{label}: {state}", cb.toggle(field))])
    buttons.append([_button(i18n.t("btn_menu"), cb.MENU)])
    return InlineKeyboardMarkup(buttons)


def history_back_actions(i18n: I18n) -> InlineKeyboardMarkup:
    buttons = [
        [_button(i18n.t("btn_history"), cb.history_list())],
        back_row(i18n),
    ]
    return InlineKeyboardMarkup(buttons)
