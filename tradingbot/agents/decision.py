"""Decision Engine.

Combines the agent scores into one directional signal. Agents are grouped
into teams with fixed weights (mirroring the V3 research spec):

    technical    (0.35) = technical 0.5 + volume 0.2 + volatility 0.15 + pattern 0.15
    market_intel (0.25) = sentiment 0.5 + onchain 0.2 + macro 0.15 + correlation 0.15
    risk         (0.20)

The directional total is the weighted team sum normalized back to -100..+100.
The sniper result is *informational* (signal-only detection of other
opportunities) and is reported but never moves the directional signal.

``confidence`` (0..100) is derived from how strongly and how unanimously the
directional agents agree.
"""

from __future__ import annotations

import math

from ..domain import Signal
from ..indicators import clamp
from .base import (
    CorrelationResult,
    DecisionResult,
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

#: Team weights for the directional signal (sniper excluded).
TEAM_WEIGHTS: dict[str, float] = {
    "technical": 0.35,
    "market_intel": 0.25,
    "risk": 0.20,
}
WITHIN_TECHNICAL: dict[str, float] = {
    "technical": 0.50,
    "volume": 0.20,
    "volatility": 0.15,
    "pattern": 0.15,
}
WITHIN_INTEL: dict[str, float] = {
    "sentiment": 0.50,
    "onchain": 0.20,
    "macro": 0.15,
    "correlation": 0.15,
}

#: Total score at/above which a signal turns BUY/SELL (below -> HOLD).
SIGNAL_THRESHOLD = 25.0

#: Confidence floor/ceiling — agreement can never claim certainty.
CONFIDENCE_MIN = 5.0
CONFIDENCE_MAX = 98.0


def _agent_overall_weights() -> dict[str, float]:
    """Per-agent share of the *directional* vote (team x intra-team, normalized)."""
    weight_sum = sum(TEAM_WEIGHTS.values())
    weights: dict[str, float] = {}
    for team, within in (("technical", WITHIN_TECHNICAL), ("market_intel", WITHIN_INTEL)):
        for name, intra in within.items():
            weights[name] = TEAM_WEIGHTS[team] * intra / weight_sum
    weights["risk"] = TEAM_WEIGHTS["risk"] / weight_sum
    return weights


def decide(
    technical: TechnicalResult,
    volume: VolumeResult,
    volatility: VolatilityResult,
    pattern: PatternResult,
    sentiment: SentimentResult,
    onchain: OnChainResult,
    macro: MacroResult,
    correlation: CorrelationResult,
    risk: RiskResult,
    sniper: SniperResult | None = None,
) -> DecisionResult:
    """Combine agent results into a total score, signal and summary."""
    scores: dict[str, float] = {
        "technical": technical.score,
        "volume": volume.score,
        "volatility": volatility.score,
        "pattern": pattern.score,
        "sentiment": sentiment.score,
        "onchain": onchain.score,
        "macro": macro.score,
        "correlation": correlation.score,
        "risk": risk.score,
    }
    weights = _agent_overall_weights()

    tech_team = sum(WITHIN_TECHNICAL[name] * scores[name] for name in WITHIN_TECHNICAL)
    intel_team = sum(WITHIN_INTEL[name] * scores[name] for name in WITHIN_INTEL)

    weight_sum = sum(TEAM_WEIGHTS.values())
    directional = (
        TEAM_WEIGHTS["technical"] * tech_team
        + TEAM_WEIGHTS["market_intel"] * intel_team
        + TEAM_WEIGHTS["risk"] * risk.score
    ) / weight_sum
    total = round(clamp(directional), 1)

    if total >= SIGNAL_THRESHOLD:
        signal = Signal.BUY
    elif total <= -SIGNAL_THRESHOLD:
        signal = Signal.SELL
    else:
        signal = Signal.HOLD

    ordered_names = list(weights)
    confidence = round(_confidence(
        [scores[name] for name in ordered_names],
        [weights[name] for name in ordered_names],
    ), 1)

    team_scores = {
        "technical": round(tech_team, 1),
        "market_intel": round(intel_team, 1),
        "risk": round(risk.score, 1),
        "sniper": round(sniper.opportunity_score, 1) if sniper else 0.0,
    }
    contributions = {
        name: round(TEAM_WEIGHTS[name] * team_scores[name] / weight_sum, 1)
        for name in TEAM_WEIGHTS
    }

    return DecisionResult(
        total_score=total,
        signal=signal.value,
        confidence=confidence,
        team_scores=team_scores,
        contributions=contributions,
        summary=_build_summary(
            technical, sentiment, risk, correlation, onchain, macro, total, signal
        ),
    )


def _confidence(scores: list[float], weights: list[float]) -> float:
    """Weighted agreement confidence: strong consensus -> high confidence.

    Uses the *same* per-agent weights as the directional vote so confidence
    reflects how the signal-contributing agents agree. ``mean=70, stdev=10``
    -> ~78; ``mean=30, stdev=30`` -> ~48.
    """
    total_weight = sum(weights)
    mean = sum(w * s for w, s in zip(weights, scores, strict=True)) / total_weight
    variance = sum(
        w * (s - mean) ** 2 for w, s in zip(weights, scores, strict=True)
    ) / total_weight
    stdev = math.sqrt(variance)
    return clamp(
        55.0 + abs(mean) * 0.45 - stdev * 1.2,
        CONFIDENCE_MIN,
        CONFIDENCE_MAX,
    )


def _build_summary(
    technical: TechnicalResult,
    sentiment: SentimentResult,
    risk: RiskResult,
    correlation: CorrelationResult,
    onchain: OnChainResult,
    macro: MacroResult,
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

    if onchain.is_demo:
        lines.append("On-chain flows are heuristic (simulated) in this build.")
    elif onchain.score != 0.0:
        direction = "supportive" if onchain.score > 0 else "negative"
        lines.append(f"On-chain flows are {direction} ({onchain.score:+.1f}/100).")

    macro_direction = "risk-on" if macro.score > 0 else "risk-off" if macro.score < 0 else "neutral"
    if macro.is_demo:
        lines.append(f"Macro backdrop {macro_direction} (simulated values).")
    else:
        lines.append(f"Macro backdrop is {macro_direction}.")

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
        lines.append("Correlation with the peer asset is not measurable right now.")

    signal_txt = (
        "Signal is BUY"
        if signal == Signal.BUY
        else "Signal is SELL"
        if signal == Signal.SELL
        else "Signal is HOLD"
    )
    lines.append(f"{signal_txt} with total score {total:+.1f}/100.")
    return " ".join(lines)