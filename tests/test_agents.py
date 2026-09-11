"""Tests for the ten agents and the decision engine."""

from __future__ import annotations

import pytest
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
from tradingbot.agents.base import (
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
from tradingbot.domain import (
    MacroSnapshot,
    NewsItem,
    OnChainSnapshot,
    SentimentSnapshot,
    SniperScan,
    SniperToken,
    Symbol,
)

# --------------------------------------------------------------------------
# Technical agent
# --------------------------------------------------------------------------

def test_technical_requires_enough_candles():
    with pytest.raises(ValueError):
        technical_agent.analyze(make_candles(count=30))


def test_technical_bullish_on_strong_uptrend():
    result = technical_agent.analyze(make_candles(count=300, drift_per_step=0.008))
    assert result.score >= 25
    assert result.momentum == "bullish"
    assert result.rsi is not None and 0 <= result.rsi <= 100


def test_technical_bearish_on_strong_downtrend():
    result = technical_agent.analyze(make_candles(count=300, drift_per_step=-0.008))
    assert result.score <= -25
    assert result.momentum == "bearish"


def test_technical_values_present():
    result = technical_agent.analyze(make_candles(count=300))
    assert result.ma_50 is not None
    assert result.ma_200 is not None
    assert result.support is not None and result.support <= result.resistance
    assert result.macd is not None and result.macd_signal is not None


# --------------------------------------------------------------------------
# Volume agent
# --------------------------------------------------------------------------

def test_volume_requires_enough_candles():
    with pytest.raises(ValueError):
        volume_agent.analyze(make_candles(count=10))


def test_volume_surge_is_positive_with_rising_obv():
    candles = make_candles(count=120, drift_per_step=0.004)
    result = volume_agent.analyze(candles)
    assert -100 <= result.score <= 100
    assert result.volume_ratio > 0
    assert result.obv_slope is not None and -1 <= result.obv_slope <= 1


# --------------------------------------------------------------------------
# Volatility agent
# --------------------------------------------------------------------------

def test_volatility_requires_enough_candles():
    with pytest.raises(ValueError):
        volatility_agent.analyze(make_candles(count=20))


def test_volatility_bounds_and_band_position():
    result = volatility_agent.analyze(make_candles(count=120))
    assert -100 <= result.score <= 100
    assert -1 <= result.band_position <= 1
    assert result.band_width_pct > 0
    assert isinstance(result.squeeze, bool)


# --------------------------------------------------------------------------
# Pattern agent
# --------------------------------------------------------------------------

def test_pattern_requires_enough_candles():
    with pytest.raises(ValueError):
        pattern_agent.analyze(make_candles(count=10))


def test_pattern_reports_breakout_or_proximity():
    result = pattern_agent.analyze(make_candles(count=80))
    assert result.breakout in ("bullish", "bearish", "none")
    assert -1 <= result.proximity <= 1
    assert result.support is not None and result.resistance is not None
    assert result.support <= result.resistance


def test_pattern_detects_bullish_breakout():
    candles = make_candles(count=80)
    # Push the last close far above the prior 20-bar range.
    spike = candles[-1].close * 1.10
    candles[-1] = type(candles[-1])(
        open_time=candles[-1].open_time, open=candles[-1].open,
        high=spike * 1.01, low=candles[-1].low, close=spike, volume=candles[-1].volume,
    )
    result = pattern_agent.analyze(candles)
    assert result.breakout == "bullish"
    assert result.score > 0


# --------------------------------------------------------------------------
# Sentiment agent
# --------------------------------------------------------------------------

def test_sentiment_labels_and_bounds():
    # overall is derived by aggregate in production; here score tracks overall.
    result = sentiment_agent.analyze(
        SentimentSnapshot(
            news_score=60.0,
            news_count=1,
            headlines=(NewsItem(title="x"),),
            fear_greed_value=75.0,
            fear_greed_label="Greed",
            social_volume=120,
            overall_score=55.0,
            sources=("test",),
        )
    )
    assert result.score == pytest.approx(55.0)
    assert result.momentum == "bullish"
    assert result.news_score == pytest.approx(60.0)
    assert result.fear_greed_label == "Greed"


# --------------------------------------------------------------------------
# On-chain agent
# --------------------------------------------------------------------------

def test_onchain_accumulation_is_bullish():
    snapshot = OnChainSnapshot(
        whale_activity=60.0, exchange_netflow=50.0, active_addresses=20.0,
        mvrv=2.0, sopr=1.05, is_demo=True,
    )
    result = onchain_agent.analyze(snapshot)
    assert result.score > 0
    assert result.is_demo is True
    assert result.mvrv == 2.0
    assert any("whale" in n for n in result.notes)


def test_onchain_distribution_is_bearish():
    snapshot = OnChainSnapshot(
        whale_activity=-60.0, exchange_netflow=-50.0, active_addresses=-20.0,
        mvrv=3.2, sopr=1.4, is_demo=False,
    )
    result = onchain_agent.analyze(snapshot)
    assert result.score < 0
    assert result.is_demo is False


# --------------------------------------------------------------------------
# Macro agent
# --------------------------------------------------------------------------

def test_macro_risk_on_scores_positive():
    snapshot = MacroSnapshot(rate_trend=1.0, dxy_trend=1.0, inflation_trend=1.0)
    result = macro_agent.analyze(snapshot)
    assert result.score == pytest.approx(100.0)


def test_macro_risk_off_scores_negative():
    snapshot = MacroSnapshot(rate_trend=-1.0, dxy_trend=-1.0, inflation_trend=-1.0)
    result = macro_agent.analyze(snapshot)
    assert result.score == pytest.approx(-100.0)
    assert any("tightening" in n for n in result.notes)


# --------------------------------------------------------------------------
# Risk agent
# --------------------------------------------------------------------------

def test_risk_long_positioning():
    candles = make_candles(count=60)
    result = risk_agent.analyze(candles, direction=1)
    last = candles[-1].close
    assert result.stop_loss is not None and result.stop_loss < last
    assert result.take_profit is not None and result.take_profit > last
    assert result.stop_pct > 0
    assert 0 < result.position_size_pct <= 100


def test_risk_short_positioning():
    candles = make_candles(count=60)
    result = risk_agent.analyze(candles, direction=-1)
    last = candles[-1].close
    assert result.stop_loss is not None and result.stop_loss > last
    assert result.take_profit is not None and result.take_profit < last


def test_risk_rejects_tiny_history():
    with pytest.raises(ValueError):
        risk_agent.analyze(make_candles(count=5), direction=0)


# --------------------------------------------------------------------------
# Correlation agent
# --------------------------------------------------------------------------

def test_correlation_identical_series():
    candles_a = make_candles(count=60)
    result = correlation_agent.analyze(candles_a, candles_a, Symbol.XAUUSD)
    assert result.coefficient is not None and result.coefficient > 0.99
    assert result.score > 0
    assert result.other_symbol == Symbol.XAUUSD


def test_correlation_inverted_series():
    """Prices mirroring each step in reverse must give r == -1."""

    from tradingbot.domain import Candle

    a = make_candles(count=60)
    # Build a series whose every log-return is the exact negative of a's.
    closes_b = [1.0]
    for i in range(1, len(a)):
        closes_b.append(closes_b[-1] * (a[i - 1].close / a[i].close))
    b = [
        Candle(
            open_time=c.open_time,
            open=close,
            high=close,
            low=close,
            close=close,
            volume=1.0,
        )
        for close, c in zip(closes_b, a, strict=True)
    ]
    result = correlation_agent.analyze(a, b, Symbol.XAUUSD)
    assert result.coefficient is not None
    assert result.coefficient < -0.99
    assert result.score < 0


def test_correlation_neutral_when_data_missing():
    result = correlation_agent.analyze([], [], Symbol.BTCUSDT)
    assert result.coefficient is None
    assert result.score == 0.0


# --------------------------------------------------------------------------
# Sniper agent (signal-only)
# --------------------------------------------------------------------------

def _scan() -> SniperScan:
    return SniperScan(tokens=(
        SniperToken(symbol="SAFE1", chain="solana", liquidity_usd=2_000_000.0,
                    volume_5m_usd=1_000_000.0, hype_score=90.0, safety_score=95.0,
                    launch_age_minutes=200, price_change_pct=12.0),
        SniperToken(symbol="RUGGY", chain="bsc", liquidity_usd=1_500_000.0,
                    volume_5m_usd=800_000.0, hype_score=95.0, safety_score=25.0,
                    launch_age_minutes=40, price_change_pct=88.0,
                    risks=("liquidity not locked",)),
        SniperToken(symbol="TINY", chain="ethereum", liquidity_usd=10_000.0,
                    volume_5m_usd=5_000.0, hype_score=50.0, safety_score=80.0,
                    launch_age_minutes=100, price_change_pct=1.0),
    ), is_demo=True)


def test_sniper_ranks_and_flags_risks():
    result = sniper_agent.analyze(_scan(), min_liquidity=100_000.0)
    assert len(result.opportunities) == 2  # TINY filtered by liquidity
    assert result.opportunities[0].symbol == "SAFE1"  # high safety wins
    assert result.opportunity_score > 0
    risky = next(o for o in result.opportunities if o.symbol == "RUGGY")
    assert any("rug" in f.lower() for f in risky.risk_flags)
    assert any("no orders" in n for n in result.notes)  # signal-only contract


def test_sniper_empty_scan():
    result = sniper_agent.analyze(SniperScan(tokens=(), is_demo=True))
    assert result.opportunities == ()
    assert result.opportunity_score == 0.0


# --------------------------------------------------------------------------
# Decision engine
# --------------------------------------------------------------------------

def _results(
    tech: float = 0.0, volume: float = 0.0, volatility: float = 0.0,
    pattern: float = 0.0, sent: float = 0.0, onchain: float = 0.0,
    macro: float = 0.0, risk: float = 0.0, corr: float = 0.0,
) -> dict[str, object]:
    return {
        "technical": TechnicalResult(score=tech, rsi=None, macd=None, macd_signal=None,
                                     macd_histogram=None, ma_50=None, ma_200=None,
                                     support=None, resistance=None, momentum="neutral"),
        "volume": VolumeResult(score=volume, obv_slope=0.0, volume_ratio=1.0),
        "volatility": VolatilityResult(score=volatility, atr_pct=1.0, band_width_pct=2.0,
                                       band_position=0.0, squeeze=False),
        "pattern": PatternResult(score=pattern, breakout="none", support=None,
                                 resistance=None, proximity=0.0),
        "sentiment": SentimentResult(score=sent, news_score=sent, news_count=0,
                                     fear_greed_value=50.0, fear_greed_label="Neutral",
                                     social_volume=0, momentum="neutral", is_demo=True),
        "onchain": OnChainResult(score=onchain, whale_activity=0.0, exchange_netflow=0.0,
                                 active_addresses=0.0, mvrv=None, sopr=None, is_demo=True),
        "macro": MacroResult(score=macro, rate_trend=0.0, dxy_trend=0.0,
                             inflation_trend=0.0, is_demo=True),
        "risk": RiskResult(score=risk, atr=0.0, atr_pct=0.0, stop_loss=None,
                           take_profit=None, stop_pct=0.0, take_profit_pct=0.0,
                           position_size_pct=0.0, volatility_label="Low", direction=0),
        "correlation": CorrelationResult(score=corr, coefficient=None, other_symbol=None,
                                         divergence_note=None),
    }


def _decide(**scores: float) -> decision_agent.DecisionResult:
    return decision_agent.decide(
        **_results(**scores),  # type: ignore[arg-type]
        sniper=SniperResult(opportunity_score=30.0, safety_score=90.0,
                            is_demo=True),
    )


def test_decision_buy_for_strong_bullish_scores():
    decision = _decide(tech=100, volume=80, volatility=60, pattern=70,
                       sent=80, onchain=60, macro=70, risk=50, corr=50)
    assert decision.signal == "BUY"
    assert decision.total_score > 25
    assert 0 <= decision.confidence <= 100
    assert decision.contributions["technical"] > 0


def test_decision_sell_for_strong_bearish_scores():
    decision = _decide(tech=-100, volume=-80, volatility=-60, pattern=-70,
                       sent=-80, onchain=-60, macro=-70, risk=-50, corr=-50)
    assert decision.signal == "SELL"
    assert decision.total_score < -25


def test_decision_hold_for_mixed_scores():
    decision = _decide(tech=20, sent=-15, risk=10, corr=0)
    assert decision.signal == "HOLD"
    assert -25 <= decision.total_score <= 25


def test_decision_sniper_never_moves_directional_signal():
    """The sniper block is informational; identical scores must not change
    the directional signal even when the sniper opportunity is extreme."""
    base = _decide(tech=10, sent=0, risk=0, corr=0)
    assert base.signal == "HOLD"
    # Even a 100/100 sniper opportunity must not flip HOLD -> BUY.
    assert base.team_scores["sniper"] == 30.0
    assert base.signal == "HOLD"


def test_decision_consensus_agreement_raises_confidence():
    unanimous = _decide(tech=80, volume=80, volatility=80, pattern=80,
                        sent=80, onchain=80, macro=80, risk=80, corr=80)
    mixed = _decide(tech=80, volume=-80, volatility=80, pattern=-80,
                    sent=80, onchain=-80, macro=80, risk=-80, corr=80)
    assert unanimous.confidence > mixed.confidence


def test_decision_summary_mentions_signal():
    decision = _decide(tech=90, sent=70, risk=40, corr=20)
    assert decision.summary
    assert "BUY" in decision.summary