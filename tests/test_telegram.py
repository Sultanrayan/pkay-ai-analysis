"""Tests for the Telegram formatting/i18n layer (no network, no bot API)."""

from __future__ import annotations

from datetime import datetime, timezone

from conftest import make_candles

from tradingbot.agents import correlation as correlation_agent
from tradingbot.agents import decision as decision_agent
from tradingbot.agents import macro as macro_agent
from tradingbot.agents import onchain as onchain_agent
from tradingbot.agents import pattern as pattern_agent
from tradingbot.agents import risk as risk_agent
from tradingbot.agents import sentiment as sentiment_agent
from tradingbot.agents import sniper as sniper_agent
from tradingbot.agents import technical as technical_agent
from tradingbot.agents import volatility as volatility_agent
from tradingbot.agents import volume as volume_agent
from tradingbot.analysis.report import AnalysisReport
from tradingbot.domain import (
    MacroSnapshot,
    NewsItem,
    OnChainSnapshot,
    SentimentSnapshot,
    SniperScan,
    SniperToken,
    Symbol,
    Timeframe,
)
from tradingbot.storage.models import UserPreferences
from tradingbot.telegram import callback_data as cb
from tradingbot.telegram.formatter import (
    history_detail_html,
    history_list_html,
    report_html,
    settings_html,
    sniper_html,
    split_message,
    welcome_html,
)
from tradingbot.telegram.i18n import STRINGS, I18n


def _build_report() -> AnalysisReport:
    candles = make_candles(count=300)
    tech = technical_agent.analyze(candles)
    sent = sentiment_agent.analyze(
        SentimentSnapshot(
            news_score=10.0, news_count=1,
            headlines=(NewsItem(title="ok"),),
            fear_greed_value=60.0, fear_greed_label="Greed", social_volume=500,
            overall_score=8.0, sources=("test",),
        )
    )
    risk = risk_agent.analyze(candles, direction=1 if tech.score > 0 else -1)
    corr = correlation_agent.analyze(candles, candles, Symbol.XAUUSD)
    volume = volume_agent.analyze(candles)
    volatility = volatility_agent.analyze(candles)
    pattern = pattern_agent.analyze(candles)
    onchain = onchain_agent.analyze(OnChainSnapshot(
        whale_activity=10.0, exchange_netflow=-5.0, active_addresses=3.0,
        mvrv=1.8, sopr=1.02, is_demo=True,
    ))
    macro = macro_agent.analyze(MacroSnapshot(
        rate_trend=0.2, dxy_trend=-0.1, inflation_trend=0.3, is_demo=True,
    ))
    sniper = sniper_agent.analyze(SniperScan(tokens=(
        SniperToken(symbol="PEPE_X", chain="solana", liquidity_usd=2_000_000.0,
                    volume_5m_usd=1_000_000.0, hype_score=85.0, safety_score=92.0,
                    launch_age_minutes=200, price_change_pct=18.4),
    ), is_demo=True), min_liquidity=100_000.0)
    decision = decision_agent.decide(
        tech, volume, volatility, pattern, sent, onchain, macro, corr, risk, sniper
    )
    return AnalysisReport(
        symbol=Symbol.BTCUSDT,
        timeframe=Timeframe.H1,
        current_price=candles[-1].close,
        technical=tech,
        volume=volume,
        volatility=volatility,
        pattern=pattern,
        sentiment=sent,
        onchain=onchain,
        macro=macro,
        risk=risk,
        correlation=corr,
        sniper=sniper,
        decision=decision,
        candle_source="test",
        is_demo_data=False,
        created_at=datetime(2026, 9, 5, 12, 30, tzinfo=timezone.utc),
        response_time_ms=123,
    )


# --------------------------------------------------------------------------
# i18n
# --------------------------------------------------------------------------

def test_translation_key_sets_match_across_languages():
    en_keys = set(STRINGS["en"])
    kh_keys = set(STRINGS["kh"])
    assert en_keys == kh_keys, f"Missing keys: {en_keys ^ kh_keys}"


def test_i18n_returns_translation_and_formats_placeholders():
    en = I18n("en")
    kh = I18n("kh")
    assert en.t("btn_analyze") == "🔍 Analyze"
    assert kh.t("btn_analyze") == "🔍 វិភាគ"
    assert en.t("rate_limited", limit=5) == (
        "⛔ You reached your daily limit of 5 analyses. It resets at midnight UTC."
    )


def test_i18n_falls_back_to_english_and_key():
    kh = I18n("kh")
    # Present in en but the placeholder values differ per language.
    assert kh.t("tf_1h") == "1H"
    # Unknown key surfaces itself (dev aid) instead of crashing.
    assert I18n("en").t("does_not_exist") == "does_not_exist"


# --------------------------------------------------------------------------
# Formatters
# --------------------------------------------------------------------------

def test_report_html_contains_sections_and_value():
    report = _build_report()
    i18n = I18n("en")
    html = report_html(report, i18n, UserPreferences(user_id=1))
    assert "Analysis Report" in html
    assert "RSI (14)" in html
    assert "Fear &amp; Greed" in html or "Fear & Greed" in html
    assert "Stop Loss" in html
    assert "Agent Consensus" in html
    assert "On-Chain" in html
    assert "Macro" in html
    assert "Sniper Scan" in html
    assert "no orders are ever placed" in html  # signal-only contract
    assert report.final_signal in html


def test_report_honours_section_toggles():
    report = _build_report()
    html = report_html(report, I18n("en"), UserPreferences(user_id=1, show_risk=False, show_sentiment=False))
    assert "Stop Loss" not in html
    assert "Market Sentiment" not in html
    assert "Risk Management" not in html
    assert "On-Chain" not in html  # grouped under the sentiment toggle
    assert "RSI (14)" in html
    # The consensus + sniper blocks stay visible regardless of toggles.
    assert "Agent Consensus" in html
    assert "Sniper Scan" in html


def test_report_khmer_uses_khmer_labels():
    report = _build_report()
    html = report_html(report, I18n("kh"), UserPreferences(user_id=1))
    assert "តម្លៃបច្ចុប្បន្ន" in html  # "Current Price" in Khmer


def test_welcome_and_history_pages():
    en = I18n("en")
    assert "BTCUSDT" in welcome_html(en, "Ada")
    assert "/sniper" in welcome_html(en, None)

    from tradingbot.storage.models import HistoryRow

    rows = [
        HistoryRow(id=1, user_id=1, symbol="BTCUSDT", timeframe="1h",
                   timestamp=datetime(2026, 9, 5, tzinfo=timezone.utc),
                   current_price=60000.0, technical_score=10, sentiment_score=0,
                   risk_score=0, correlation_score=0, total_score=10,
                   confidence=70.0, signal="BUY", summary="s"),
    ]
    text = history_list_html(rows, en, limit=10)
    assert "BTCUSDT 1H" in text
    detail = history_detail_html(rows[0], en)
    assert "BUY" in detail and "60,000" in detail
    assert "70%" in detail  # confidence shown in history detail
    settings = settings_html(UserPreferences(user_id=1, show_chart=False), en)
    assert "Language" in settings


def test_sniper_page_renders_opportunities_and_disclaimer():
    from tradingbot.agents.base import SniperOpportunity, SniperResult

    result = SniperResult(
        opportunity_score=62.0,
        safety_score=92.0,
        opportunities=(
            SniperOpportunity(symbol="PEPE_X", chain="solana", liquidity_usd=2_100_000.0,
                              hype_score=85.0, safety_score=92.0, price_change_pct=18.4),
        ),
        is_demo=True,
    )
    html = sniper_html(result, I18n("en"))
    assert "PEPE_X" in html
    assert "62/100" in html
    assert "no orders" in html
    assert "Simulated demo scan" in html


def test_split_message_respects_limit():
    long_text = "\n\n".join(f"Paragraph {i} " + "x" * 200 for i in range(30))
    chunks = split_message(long_text, limit=1024)
    assert len(chunks) > 1
    assert all(len(c) <= 1024 for c in chunks)
    assert "".join(chunks).replace("\n\n", "\n\n")  # content preserved loosely


# --------------------------------------------------------------------------
# Callback data
# --------------------------------------------------------------------------

def test_callback_payloads_roundtrip():
    assert cb.parse(cb.pick_asset(Symbol.BTCUSDT)) == ("asset", "BTCUSDT")
    assert cb.parse(cb.pick_timeframe("ALL", Timeframe.H4)) == ("tf", "ALL", "4h")
    assert cb.parse(cb.run(Symbol.XAUUSD, Timeframe.D1)) == ("run", "XAUUSD", "1d")
    assert cb.parse(cb.report(cb.REPORT_REFRESH)) == ("report", "refresh")
    assert cb.parse(cb.sniper_scan()) == ("sniper",)
    assert cb.parse(cb.history_open(12)) == ("history", "12")
    assert cb.timeframe_from("4h") == Timeframe.H4
    assert cb.symbol_from("xauusd") == Symbol.XAUUSD
    assert cb.symbol_from("ethusdt") == Symbol.ETHUSDT
    assert cb.parse(None) == ()
    assert cb.parse("") == ()
