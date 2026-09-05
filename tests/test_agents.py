"""Tests for the four agents and the decision engine."""

from __future__ import annotations

import pytest
from conftest import make_candles

from tradingbot.agents import correlation as correlation_agent
from tradingbot.agents import decision as decision_agent
from tradingbot.agents import risk as risk_agent
from tradingbot.agents import sentiment as sentiment_agent
from tradingbot.agents import technical as technical_agent
from tradingbot.agents.base import (
    CorrelationResult,
    RiskResult,
    SentimentResult,
    TechnicalResult,
)
from tradingbot.domain import NewsItem, SentimentSnapshot, Symbol

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
    result = correlation_agent.analyze([], [], Symbol.BTCUSD)
    assert result.coefficient is None
    assert result.score == 0.0


# --------------------------------------------------------------------------
# Decision engine
# --------------------------------------------------------------------------

def _results(
    tech: float = 0.0, sent: float = 0.0, risk: float = 0.0, corr: float = 0.0
) -> tuple[TechnicalResult, SentimentResult, RiskResult, CorrelationResult]:
    return (
        TechnicalResult(score=tech, rsi=None, macd=None, macd_signal=None,
                        macd_histogram=None, ma_50=None, ma_200=None,
                        support=None, resistance=None, momentum="neutral"),
        SentimentResult(score=sent, news_score=sent, news_count=0,
                        fear_greed_value=50.0, fear_greed_label="Neutral",
                        social_volume=0, momentum="neutral", is_demo=True),
        RiskResult(score=risk, atr=0.0, atr_pct=0.0, stop_loss=None,
                   take_profit=None, stop_pct=0.0, take_profit_pct=0.0,
                   position_size_pct=0.0, volatility_label="Low", direction=0),
        CorrelationResult(score=corr, coefficient=None, other_symbol=None,
                          divergence_note=None),
    )


def test_decision_buy_for_strong_bullish_scores():
    decision = decision_agent.decide(*_results(tech=100, sent=80, risk=50, corr=50))
    assert decision.signal == "BUY"
    assert decision.total_score > 25
    assert decision.contributions["technical"] == pytest.approx(40.0)


def test_decision_sell_for_strong_bearish_scores():
    decision = decision_agent.decide(*_results(tech=-100, sent=-80, risk=-50, corr=-50))
    assert decision.signal == "SELL"
    assert decision.total_score < -25


def test_decision_hold_for_mixed_scores():
    decision = decision_agent.decide(*_results(tech=20, sent=-15, risk=10, corr=0))
    assert decision.signal == "HOLD"
    assert -25 <= decision.total_score <= 25


def test_decision_summary_mentions_signal():
    decision = decision_agent.decide(*_results(tech=90, sent=70, risk=40, corr=20))
    assert decision.summary
    assert "BUY" in decision.summary
