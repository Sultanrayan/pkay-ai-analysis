"""Macro Economics Agent.

Scores a :class:`~tradingbot.domain.MacroSnapshot` into a directional read
for risk assets: easing central-bank policy, a weaker dollar and
disinflation all support risk-on positioning, and the reverse is risk-off.
Without a configured economic data feed the manager serves deterministic
demo values (flagged), so this agent is a pure function either way.
"""

from __future__ import annotations

from ..domain import MacroSnapshot
from ..indicators import clamp
from .base import MacroResult


def analyze(snapshot: MacroSnapshot) -> MacroResult:
    """Score the macro backdrop from ``snapshot``."""
    raw = (snapshot.rate_trend + snapshot.dxy_trend + snapshot.inflation_trend) / 3.0

    notes: list[str] = []
    if snapshot.rate_trend >= 0.5:
        notes.append("easing bias — supportive for risk assets")
    elif snapshot.rate_trend <= -0.5:
        notes.append("tightening bias — headwind for risk assets")
    if snapshot.dxy_trend >= 0.5:
        notes.append("dollar weakening — supportive for crypto/gold")
    elif snapshot.dxy_trend <= -0.5:
        notes.append("dollar strengthening — headwind for crypto/gold")
    if snapshot.inflation_trend >= 0.5:
        notes.append("disinflation — supportive for duration/risk assets")
    elif snapshot.inflation_trend <= -0.5:
        notes.append("inflation re-accelerating — headwind for risk assets")
    if snapshot.is_demo:
        notes.append("macro data is simulated — connect a live economic feed for real readings")
    if not notes:
        notes.append("macro backdrop broadly neutral")

    return MacroResult(
        score=round(clamp(raw * 100.0), 1),
        rate_trend=round(snapshot.rate_trend, 2),
        dxy_trend=round(snapshot.dxy_trend, 2),
        inflation_trend=round(snapshot.inflation_trend, 2),
        is_demo=snapshot.is_demo,
        notes=tuple(notes),
    )