"""Memecoin Sniper Agent (signal-only).

Ranks candidates from a :class:`~tradingbot.domain.SniperScan` into a
short list of opportunities using a transparent weighted formula:

    opportunity = 0.35*hype + 0.30*liquidity + 0.20*volume + 0.15*safety

Candidates failing the minimum-liquidity filter are dropped, and a low
safety score (rug risk) is surfaced as a hard risk flag rather than hidden.

**This agent never places orders** — it only reports opportunities and their
risk profile. Executing trades is out of scope by design.
"""

from __future__ import annotations

from ..domain import SniperScan, SniperToken
from ..indicators import clamp
from .base import SniperOpportunity, SniperResult

#: Opportunity weighting (sums to 1.0).
W_HYPE = 0.35
W_LIQUIDITY = 0.30
W_VOLUME = 0.20
W_SAFETY = 0.15

#: $100k floor for the liquidity sub-score (log-ish curve, 0..100).
LIQUIDITY_REFERENCE = 100_000.0
#: $250k floor for the volume sub-score.
VOLUME_REFERENCE = 250_000.0
#: Below this safety score a token is flagged as high-risk regardless of hype.
SAFETY_WARNING = 60.0


def _sub_score(value: float, reference: float) -> float:
    """Diminishing-returns map of a dollar figure onto 0..100."""
    if value <= 0:
        return 0.0
    return clamp(100.0 * (1.0 - reference / (reference + value)), 0.0, 100.0)


def _opportunity(token: SniperToken, min_liquidity: float) -> SniperOpportunity | None:
    """Score one token; ``None`` when it fails the liquidity filter."""
    if token.liquidity_usd < min_liquidity:
        return None
    risk_flags: list[str] = []
    if token.safety_score < SAFETY_WARNING:
        risk_flags.append("low safety score — high rug risk")
    risk_flags.extend(token.risks)
    return SniperOpportunity(
        symbol=token.symbol,
        chain=token.chain,
        liquidity_usd=token.liquidity_usd,
        hype_score=round(token.hype_score, 1),
        safety_score=round(token.safety_score, 1),
        price_change_pct=round(token.price_change_pct, 1),
        risk_flags=tuple(risk_flags),
    )


def _opportunity_score(opp: SniperOpportunity) -> float:
    """Recompute the weighted score for a ranked opportunity."""
    return (
        W_HYPE * opp.hype_score
        + W_LIQUIDITY * _sub_score(opp.liquidity_usd, LIQUIDITY_REFERENCE)
        + W_VOLUME * _sub_score(opp.liquidity_usd, VOLUME_REFERENCE)
        + W_SAFETY * opp.safety_score
    )


def analyze(
    scan: SniperScan,
    min_liquidity: float = 500_000.0,
    max_opportunities: int = 3,
) -> SniperResult:
    """Rank ``scan``'s tokens and return the top opportunities."""
    ranked = sorted(
        (
            opp
            for token in scan.tokens
            if (opp := _opportunity(token, min_liquidity)) is not None
        ),
        key=_opportunity_score,
        reverse=True,
    )[: max(0, max_opportunities)]

    notes: list[str] = []
    if not ranked:
        notes.append("no candidates passed the liquidity filter")
    elif ranked[0].risk_flags:
        notes.append("top candidate carries risk flags — treat with caution")
    if scan.is_demo:
        notes.append("scan uses simulated demo data — connect DEX Screener/Raydium for live detection")
    notes.append("signal-only — no orders are ever placed")

    opportunity_score = _opportunity_score(ranked[0]) if ranked else 0.0

    return SniperResult(
        opportunity_score=round(opportunity_score, 1),
        safety_score=round(ranked[0].safety_score, 1) if ranked else 0.0,
        opportunities=tuple(ranked),
        is_demo=scan.is_demo,
        notes=tuple(notes),
    )