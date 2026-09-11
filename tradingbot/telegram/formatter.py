"""Message formatters.

Turn reports/history/settings into Telegram HTML strings. Formatting is kept
out of the handlers so every message is easy to preview and unit test.
Dynamic user-provided values must be HTML-escaped by the caller.
"""

from __future__ import annotations

from html import escape

from telegram.constants import MessageLimit

from ..agents.base import (
    CorrelationResult,
    MacroResult,
    OnChainResult,
    PatternResult,
    RiskResult,
    SentimentResult,
    SniperResult,
    TechnicalResult,
    VolatilityResult,
    VolumeResult,
)
from ..analysis.report import AnalysisReport
from ..domain import Signal
from ..storage.models import HistoryRow, UserPreferences
from .i18n import I18n

SEPARATOR = "━━━━━━━━━━━━━━━━━━━━━"
BAR_WIDTH = 10
FILL = "█"
EMPTY = "░"

SIGNAL_EMOJI = {
    Signal.BUY.value: "🟢",
    Signal.SELL.value: "🔴",
    Signal.HOLD.value: "🟡",
}

#: team_scores keys -> i18n label key for the consensus block (short labels
#: so they never collide with the collapsible report section headers).
TEAM_LABELS = {
    "technical": "lbl_team_technical",
    "market_intel": "lbl_team_intel",
    "risk": "lbl_team_risk",
    "sniper": "lbl_team_sniper",
}


def money(value: float | None, decimals: int = 2) -> str:
    """Currency display with thousands separators."""
    if value is None:
        return "—"
    return f"${value:,.{decimals}f}"


def signed(value: float | None, decimals: int = 1) -> str:
    """Signed number display used for scores."""
    if value is None:
        return "—"
    return f"{value:+.{decimals}f}"


def signal_with_emoji(signal: str | None) -> str:
    if not signal:
        return "—"
    emoji = SIGNAL_EMOJI.get(signal.upper(), "")
    return f"{emoji} {signal.upper()}" if emoji else signal.upper()


def progress_bar(percent: float, width: int = BAR_WIDTH) -> str:
    """10-block progress bar for a 0..100 percentage."""
    percent = max(0.0, min(100.0, percent))
    filled = round(percent / 100.0 * width)
    return FILL * filled + EMPTY * (width - filled)


# --------------------------------------------------------------------------
# Static pages
# --------------------------------------------------------------------------

def welcome_html(i18n: I18n, first_name: str | None) -> str:
    name = escape(first_name) if first_name else ""
    greeting = f"<b>{i18n.t('welcome_title')}</b>"
    if name:
        greeting = f"<b>👋 {name}</b>\n\n" + i18n.t("welcome_title")
    return f"{greeting}\n\n{i18n.t('welcome_body')}"


def help_html(i18n: I18n, max_daily_requests: int) -> str:
    return (
        f"<b>{i18n.t('help_title')}</b>\n\n"
        f"{i18n.t('help_body', limit=max_daily_requests)}"
    )


def about_html(i18n: I18n, version: str) -> str:
    return i18n.t("about_text", version=version)


# --------------------------------------------------------------------------
# Analysis report
# --------------------------------------------------------------------------

def report_html(
    report: AnalysisReport,
    i18n: I18n,
    preferences: UserPreferences | None = None,
) -> str:
    """Render a fresh analysis report honouring the user's section toggles."""
    prefs = preferences or _default_prefs()
    lines: list[str] = []
    symbol_label = report.symbol.value
    timeframe_label = report.timeframe.value.upper()
    lines.append(f"📊 <b>{i18n.t('report_title', symbol=symbol_label)}</b>")
    lines.append(
        f"{i18n.t('lbl_time')}: {report.created_at:%d/%m/%Y %H:%M} UTC · "
        f"{i18n.t('lbl_timeframe')}: <code>{timeframe_label}</code>"
    )
    if report.signal_source == "ai":
        lines.append(i18n.t("ai_enhanced"))
    lines.append(SEPARATOR)
    lines.append(
        f"💰 <b>{i18n.t('lbl_price')}:</b> {money(report.current_price)}\n"
        f"{i18n.t('lbl_signal')}: <b>{signal_with_emoji(report.final_signal)}</b> "
        f"({i18n.t('lbl_score')}: {report.decision.total_score:+.0f}/100 · "
        f"{i18n.t('lbl_confidence')}: {report.final_confidence:.0f}%)"
    )

    # -- Agent consensus ------------------------------------------------
    lines.append(SEPARATOR)
    lines.append(f"<b>{i18n.t('sec_consensus')}</b> ({len(report.decision.team_scores)} teams)")
    lines.extend(_consensus_lines(report, i18n))

    # -- Technical indicators ---------------------------------------------
    if prefs.show_indicators:
        lines.extend(_technical_lines(report, i18n))

    # -- Sentiment ---------------------------------------------------------
    if prefs.show_sentiment:
        lines.extend(_sentiment_lines(report.sentiment, i18n))
        lines.extend(_onchain_lines(report.onchain, i18n))
        lines.extend(_macro_lines(report.macro, i18n))

    # -- Risk management ---------------------------------------------------
    if prefs.show_risk:
        lines.extend(_risk_lines(report.risk, i18n))

    # -- Correlation -------------------------------------------------------
    lines.extend(_correlation_lines(report.correlation, i18n))

    # -- Sniper scan -------------------------------------------------------
    lines.extend(_sniper_lines(report.sniper, i18n))

    lines.append(SEPARATOR)
    lines.append(f"<b>{i18n.t('sec_summary')}</b>")
    lines.append(escape(report.final_summary))

    if report.demo_sources:
        lines.append("")
        lines.append(i18n.t("demo_notice", sources=", ".join(report.demo_sources)))
    return "\n".join(lines)


def _default_prefs() -> UserPreferences:
    return UserPreferences(user_id=0)


def _bullet(label: str, value: str) -> str:
    """One bullet line; both sides HTML-escaped (labels may contain ``&``)."""
    return f"• <b>{escape(label)}:</b> {escape(value)}"


def _consensus_lines(report: AnalysisReport, i18n: I18n) -> list[str]:
    """Per-team progress bars: how aligned each team is (0..100%)."""
    lines: list[str] = []
    for key, score in report.decision.team_scores.items():
        label = i18n.t(TEAM_LABELS.get(key, key))
        if key == "sniper":
            percent = max(0.0, min(100.0, score))
            detail = i18n.t("lbl_opportunity")
        else:
            percent = (max(-100.0, min(100.0, score)) + 100.0) / 2.0
            detail = signed(score)
        lines.append(f"{label}: <code>{progress_bar(percent)}</code> {percent:.0f}% ({detail})")
    return lines


def _technical_lines(report: AnalysisReport, i18n: I18n) -> list[str]:
    technical: TechnicalResult = report.technical
    volume: VolumeResult = report.volume
    volatility: VolatilityResult = report.volatility
    pattern: PatternResult = report.pattern
    lines = [SEPARATOR, f"<b>{i18n.t('sec_technical')}</b>"]
    lines.append(_bullet(i18n.t("lbl_rsi"), f"{technical.rsi:.1f}" if technical.rsi is not None else i18n.t("na")))
    lines.append(_bullet(i18n.t("lbl_macd"), f"{technical.macd:.6f}" if technical.macd is not None else i18n.t("na")))
    lines.append(_bullet(i18n.t("lbl_ma50"), money(technical.ma_50)))
    lines.append(_bullet(i18n.t("lbl_ma200"), money(technical.ma_200)))
    lines.append(_bullet(i18n.t("lbl_volume"), f"{volume.volume_ratio:.2f}x avg"))
    lines.append(_bullet(i18n.t("lbl_obv"), signed(volume.obv_slope * 100.0, 0)))
    lines.append(_bullet(
        i18n.t("lbl_volatility"),
        f"{volatility.band_width_pct:.1f}% band" + (" · " + i18n.t("lbl_squeeze") if volatility.squeeze else ""),
    ))
    lines.append(_bullet(i18n.t("lbl_pattern"), pattern.breakout if pattern.breakout != "none" else i18n.t("na")))
    lines.append(_bullet(i18n.t("lbl_support"), money(technical.support)))
    lines.append(_bullet(i18n.t("lbl_resistance"), money(technical.resistance)))
    return lines


def _sentiment_lines(sentiment: SentimentResult, i18n: I18n) -> list[str]:
    lines = [SEPARATOR, f"<b>{i18n.t('sec_sentiment')}</b>"]
    lines.append(_bullet(
        i18n.t("lbl_news"), f"{signed(sentiment.news_score)} ({sentiment.news_count} {i18n.t('lbl_headlines').lower()})"
    ))
    lines.append(_bullet(
        i18n.t("lbl_fng"), f"{sentiment.fear_greed_value:.0f} ({sentiment.fear_greed_label})"
    ))
    lines.append(_bullet(i18n.t("lbl_social"), f"{sentiment.social_volume:,}"))
    return lines


def _onchain_lines(onchain: OnChainResult, i18n: I18n) -> list[str]:
    lines = [SEPARATOR, f"<b>{i18n.t('sec_onchain')}</b>"]
    lines.append(_bullet(i18n.t("lbl_whale"), signed(onchain.whale_activity)))
    lines.append(_bullet(i18n.t("lbl_netflow"), signed(onchain.exchange_netflow)))
    lines.append(_bullet(i18n.t("lbl_active"), signed(onchain.active_addresses)))
    lines.append(_bullet(i18n.t("lbl_mvrv"), f"{onchain.mvrv:.2f}" if onchain.mvrv is not None else i18n.t("na")))
    lines.append(_bullet(i18n.t("lbl_sopr"), f"{onchain.sopr:.3f}" if onchain.sopr is not None else i18n.t("na")))
    return lines


def _macro_lines(macro: MacroResult, i18n: I18n) -> list[str]:
    lines = [SEPARATOR, f"<b>{i18n.t('sec_macro')}</b>"]
    lines.append(_bullet(i18n.t("lbl_rate"), signed(macro.rate_trend * 100.0, 0)))
    lines.append(_bullet(i18n.t("lbl_dxy"), signed(macro.dxy_trend * 100.0, 0)))
    lines.append(_bullet(i18n.t("lbl_inflation"), signed(macro.inflation_trend * 100.0, 0)))
    return lines


def _risk_lines(risk: RiskResult, i18n: I18n) -> list[str]:
    lines = [SEPARATOR, f"<b>{i18n.t('sec_risk')}</b>"]
    lines.append(_bullet(i18n.t("lbl_sl"), money(risk.stop_loss)))
    lines.append(_bullet(i18n.t("lbl_tp"), money(risk.take_profit)))
    lines.append(_bullet(i18n.t("lbl_pos"), f"{risk.position_size_pct:.1f}%"))
    lines.append(_bullet(i18n.t("lbl_vol"), f"{risk.atr_pct:.2f}% ({risk.volatility_label})"))
    lines.append(_bullet(i18n.t("lbl_atr"), f"{risk.atr:.6f}"))
    return lines


def _correlation_lines(correlation: CorrelationResult, i18n: I18n) -> list[str]:
    lines = [SEPARATOR, f"<b>{i18n.t('sec_correlation')}</b>"]
    if correlation.coefficient is None:
        lines.append(_bullet(i18n.t("lbl_corr"), i18n.t("na")))
        if correlation.divergence_note:
            lines.append(f"<i>{escape(correlation.divergence_note)}</i>")
    else:
        other = correlation.other_symbol.value if correlation.other_symbol else ""
        lines.append(_bullet(i18n.t("lbl_corr"), f"r = {correlation.coefficient:+.2f} ({other})"))
        if correlation.divergence_note:
            lines.append(f"<i>{escape(correlation.divergence_note)}</i>")
    return lines


def _sniper_lines(sniper: SniperResult, i18n: I18n) -> list[str]:
    lines = [SEPARATOR, f"<b>{i18n.t('sec_sniper')}</b>"]
    if not sniper.opportunities:
        lines.append(_bullet(i18n.t("lbl_opportunity"), i18n.t("sniper_empty")))
    else:
        lines.append(_bullet(
            i18n.t("lbl_opportunity"),
            f"{sniper.opportunity_score:.0f}/100 · {i18n.t('lbl_safety')} {sniper.safety_score:.0f}/100",
        ))
        for opp in sniper.opportunities:
            flags = ", ".join(opp.risk_flags) if opp.risk_flags else i18n.t("na")
            lines.append(_bullet(
                f"{opp.symbol} ({opp.chain})",
                f"{i18n.t('lbl_liquidity')} {money(opp.liquidity_usd, 0)} · "
                f"{i18n.t('lbl_hype')} {opp.hype_score:.0f} · "
                f"{i18n.t('lbl_safety')} {opp.safety_score:.0f} · "
                f"{opp.price_change_pct:+.1f}%",
            ))
            if opp.risk_flags:
                lines.append(f"  ⚠️ <b>{escape(i18n.t('lbl_risk_flags'))}:</b> {escape(flags)}")
    lines.append(i18n.t("sniper_disclaimer"))
    return lines


# --------------------------------------------------------------------------
# Sniper scan page (standalone /sniper command)
# --------------------------------------------------------------------------

def sniper_html(result: SniperResult, i18n: I18n) -> str:
    """Standalone sniper scan page rendered by /sniper."""
    lines = [f"<b>{i18n.t('sniper_title')}</b>", SEPARATOR]
    if result.is_demo:
        lines.append("⚠️ <i>Simulated demo scan — connect DEX Screener/Raydium for live data.</i>")
        lines.append(SEPARATOR)
    if not result.opportunities:
        lines.append(i18n.t("sniper_empty"))
    else:
        lines.append(_bullet(
            i18n.t("lbl_opportunity"),
            f"{result.opportunity_score:.0f}/100 · {i18n.t('lbl_safety')} {result.safety_score:.0f}/100",
        ))
        for opp in result.opportunities:
            flags = ", ".join(opp.risk_flags) if opp.risk_flags else i18n.t("na")
            lines.append(SEPARATOR)
            lines.append(f"<b>{escape(opp.symbol)}</b> · {escape(opp.chain)}")
            lines.append(_bullet(i18n.t("lbl_liquidity"), money(opp.liquidity_usd, 0)))
            lines.append(_bullet(i18n.t("lbl_hype"), f"{opp.hype_score:.0f}/100"))
            lines.append(_bullet(i18n.t("lbl_safety"), f"{opp.safety_score:.0f}/100"))
            lines.append(_bullet(i18n.t("lbl_breakout"), f"{opp.price_change_pct:+.1f}%"))
            lines.append(_bullet(i18n.t("lbl_risk_flags"), flags if flags else "—"))
    lines.append(SEPARATOR)
    lines.append(i18n.t("sniper_disclaimer"))
    return "\n".join(lines)


# --------------------------------------------------------------------------
# History (from stored rows)
# --------------------------------------------------------------------------

def history_list_html(rows: list[HistoryRow], i18n: I18n, limit: int) -> str:
    """Compact list of past analyses (details live behind their buttons)."""
    if not rows:
        return i18n.t("history_empty")
    lines = [f"<b>{i18n.t('history_title', limit=limit)}</b>"]
    for index, row in enumerate(rows, start=1):
        stamp = row.timestamp.strftime("%d/%m %H:%M") if row.timestamp else ""
        score = f" · <code>{row.total_score:+.0f}</code>" if row.total_score is not None else ""
        lines.append(
            f"{index}. {signal_with_emoji(row.signal)} <b>{row.symbol} {row.timeframe.upper()}</b>"
            f" · {stamp}{score}"
        )
    return "\n".join(lines)


def history_detail_html(row: HistoryRow, i18n: I18n) -> str:
    """Full detail of one stored analysis (no chart, uses persisted fields)."""
    lines = [
        f"📊 <b>{i18n.t('report_title', symbol=row.symbol)}</b>",
        (
            f"{i18n.t('lbl_time')}: {row.timestamp:%d/%m/%Y %H:%M} UTC · "
            f"{i18n.t('lbl_timeframe')}: <code>{row.timeframe.upper()}</code>"
        ),
        SEPARATOR,
        (
            f"💰 <b>{i18n.t('lbl_price')}:</b> {money(row.current_price)}\n"
            f"{i18n.t('lbl_signal')}: <b>{signal_with_emoji(row.signal)}</b> "
            f"({i18n.t('lbl_score')}: {row.total_score:+.0f}/100"
            + (f" · {i18n.t('lbl_confidence')}: {row.confidence:.0f}%" if row.confidence is not None else "")
            + ")"
        ),
        SEPARATOR,
        f"<b>{i18n.t('sec_technical')}</b>",
        _bullet(i18n.t("lbl_rsi"), f"{row.rsi:.1f}" if row.rsi is not None else i18n.t("na")),
        _bullet(i18n.t("lbl_macd"), f"{row.macd:.6f}" if row.macd is not None else i18n.t("na")),
        _bullet(i18n.t("lbl_support"), money(row.support)),
        _bullet(i18n.t("lbl_resistance"), money(row.resistance)),
        SEPARATOR,
        f"<b>{i18n.t('sec_risk')}</b>",
        _bullet(i18n.t("lbl_sl"), money(row.stop_loss)),
        _bullet(i18n.t("lbl_tp"), money(row.take_profit)),
        _bullet(
            i18n.t("lbl_pos"),
            f"{row.position_size_pct:.1f}%" if row.position_size_pct is not None else i18n.t("na"),
        ),
        SEPARATOR,
        f"<b>{i18n.t('sec_summary')}</b>",
        escape(row.summary or ""),
    ]
    return "\n".join(line for line in lines if line)


def settings_html(prefs: UserPreferences, i18n: I18n) -> str:
    """Settings panel describing the current preferences."""
    current_lang = i18n.t("lang_kh") if i18n.is_khmer else i18n.t("lang_en")

    def state(enabled: bool) -> str:
        return i18n.t("value_on") if enabled else i18n.t("value_off")

    lines = [
        f"<b>{i18n.t('settings_title')}</b>",
        "",
        _bullet(i18n.t("settings_lang"), current_lang),
        _bullet(i18n.t("settings_chart"), state(prefs.show_chart)),
        _bullet(i18n.t("settings_indicators"), state(prefs.show_indicators)),
        _bullet(i18n.t("settings_risk"), state(prefs.show_risk)),
        _bullet(i18n.t("settings_sentiment"), state(prefs.show_sentiment)),
    ]
    return "\n".join(lines)


def split_message(text: str, limit: int = MessageLimit.MAX_TEXT_LENGTH) -> list[str]:
    """Split long HTML text on paragraph boundaries to fit Telegram's limit."""
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) > limit:
            if current:
                parts.append(current)
                current = ""
            # Fall back to hard chunking for oversized single paragraphs.
            while len(paragraph) > limit:
                parts.append(paragraph[:limit])
                paragraph = paragraph[limit:]
            current = paragraph
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts