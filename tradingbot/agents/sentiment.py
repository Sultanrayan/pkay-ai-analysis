"""Sentiment Analysis Agent.

Packages a :class:`~tradingbot.domain.SentimentSnapshot` (news headline
scores + Fear & Greed index + social volume heuristic) into a directional
result for the decision engine.
"""

from __future__ import annotations

from ..domain import SentimentSnapshot
from ..indicators import clamp
from .base import SentimentResult

_MOMENTUM_THRESHOLD = 15.0


def analyze(snapshot: SentimentSnapshot) -> SentimentResult:
    score = round(clamp(snapshot.overall_score), 1)
    momentum = (
        "bullish"
        if score >= _MOMENTUM_THRESHOLD
        else "bearish"
        if score <= -_MOMENTUM_THRESHOLD
        else "neutral"
    )

    notes: list[str] = []
    notes.append(
        f"news {snapshot.news_score:+.1f} across {snapshot.news_count} headlines"
    )
    fng = snapshot.fear_greed_value
    notes.append(f"fear & greed {fng:.0f} ({snapshot.fear_greed_label})")
    if snapshot.is_demo:
        notes.append("sentiment source is simulated demo data")
    if snapshot.news_count == 0:
        notes.append("no symbol-specific headlines scored")

    return SentimentResult(
        score=score,
        news_score=round(snapshot.news_score, 2),
        news_count=snapshot.news_count,
        fear_greed_value=round(fng, 1),
        fear_greed_label=snapshot.fear_greed_label,
        social_volume=snapshot.social_volume,
        momentum=momentum,
        is_demo=snapshot.is_demo,
        notes=tuple(notes),
    )
