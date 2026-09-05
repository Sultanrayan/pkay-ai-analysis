"""Decision Engine.

Combines the four agent scores into one total score and trading signal using
the weights documented in the README:

    total = technical x 0.4 + sentiment x 0.3 + risk x 0.2 + correlation x 0.1

Also builds the persisted/displayed English summary paragraph from each
agent's outcome.
"""

from __future__ import annotations

from ..domain import Signal
from ..indicators import clamp
from .base import (
    CorrelationResult,
    DecisionResult,
    RiskResult,
    SentimentResult,
    TechnicalResult,
)

WEIGHTS: dict[str, float] = {
    "technical": 0.4,
    "sentiment": 0.3,
    "risk": 0.2,
    "correlation": 0.1,
}

#: Total score at/above which a signal turns BUY/SELL (below -> HOLD).
SIGNAL_THRESHOLD = 25.0


def decide(
    technical: TechnicalResult,
    sentiment: SentimentResult,
    risk: RiskResult,
    correlation: CorrelationResult,
) -> DecisionResult:
    """Combine agent results into a total score, signal and summary."""
    scores = {
        "technical": technical.score,
        "sentiment": sentiment.score,
        "risk": risk.score,
        "correlation": correlation.score,
    }
    total = round(clamp(sum(WEIGHTS[name] * scores[name] for name in WEIGHTS)), 1)

    if total >= SIGNAL_THRESHOLD:
        signal = Signal.BUY
    elif total <= -SIGNAL_THRESHOLD:
        signal = Signal.SELL
    else:
        signal = Signal.HOLD

    contributions = {name: round(WEIGHTS[name] * scores[name], 1) for name in WEIGHTS}
    return DecisionResult(
        total_score=total,
        signal=signal.value,
        contributions=contributions,
        summary=_build_summary(technical, sentiment, risk, correlation, total, signal),
    )


def _build_summary(
    technical: TechnicalResult,
    sentiment: SentimentResult,
    risk: RiskResult,
    correlation: CorrelationResult,
    total: float,
    signal: Signal,
) -> str:
    """Compose the human readable report summary (English, plain text)."""
    lines: list[str] = []

    tech_txt = f"Technical view is {technical.momentum}"
    if technical.rsi is not None:
        tech_txt += f" (RSI {technical.rsi:.1f})"
    if technical.ma_50 is not None:
        side = "above" if technical.score >= 0 else "below"
        tech_txt += f", price {side} the 50-period average"
    lines.append(tech_txt + ".")

    if sentiment.is_demo:
        sent_txt = "Sentiment from simulated demo feed"
    else:
        sent_txt = f"News sentiment {sentiment.news_score:+.1f}"
    if sentiment.fear_greed_label:
        sent_txt += f", Fear & Greed {sentiment.fear_greed_value:.0f} ({sentiment.fear_greed_label})"
    lines.append(sent_txt + ".")

    stop = f"{risk.stop_loss:,.2f}" if risk.stop_loss is not None else "n/a"
    target = f"{risk.take_profit:,.2f}" if risk.take_profit is not None else "n/a"
    lines.append(
        f"Volatility {risk.atr_pct:.2f}%/candle ({risk.volatility_label}); "
        f"suggested stop at {stop} and target at "
        f"{target} with ~{risk.position_size_pct:.1f}% position."
    )

    if correlation.coefficient is not None:
        other = correlation.other_symbol.value if correlation.other_symbol else "other asset"
        lines.append(
            f"Correlation with {other} is r={correlation.coefficient:+.2f} "
            f"({correlation.score:+.1f}/100 contribution)."
        )
    else:
        lines.append("Correlation with the other asset is not measurable right now.")

    signal_txt = (
        "Signal is BUY"
        if signal == Signal.BUY
        else "Signal is SELL"
        if signal == Signal.SELL
        else "Signal is HOLD"
    )
    lines.append(f"{signal_txt} with total score {total:+.1f}/100.")
    return " ".join(lines)
