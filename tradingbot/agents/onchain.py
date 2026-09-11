"""On-Chain Analysis Agent.

Scores a :class:`~tradingbot.domain.OnChainSnapshot` into a directional
signal: whale accumulation, exchange outflows and growing active-address
trends are bullish; the opposite is bearish. MVRV and SOPR are reported as
context (overbought/undervalued reads) rather than double-counted into the
score.
"""

from __future__ import annotations

from ..domain import OnChainSnapshot
from ..indicators import clamp
from .base import OnChainResult

#: MVRV above this suggests the market is overextended vs realized value.
MVRV_HOT = 3.0
#: SOPR above this suggests profit-taking pressure is elevated.
SOPR_HOT = 1.2


def analyze(snapshot: OnChainSnapshot) -> OnChainResult:
    """Score the on-chain picture from ``snapshot``."""
    points = (
        snapshot.whale_activity * 0.4
        + snapshot.exchange_netflow * 0.4
        + snapshot.active_addresses * 0.2
    )

    notes: list[str] = []
    if snapshot.whale_activity >= 20.0:
        notes.append("whale accumulation detected")
    elif snapshot.whale_activity <= -20.0:
        notes.append("whale distribution detected")
    if snapshot.exchange_netflow >= 20.0:
        notes.append("exchange outflows — supply leaving exchanges")
    elif snapshot.exchange_netflow <= -20.0:
        notes.append("exchange inflows — supply hitting exchanges")
    if snapshot.mvrv is not None:
        state = "overextended" if snapshot.mvrv >= MVRV_HOT else "fairly valued"
        notes.append(f"MVRV {snapshot.mvrv:.2f} ({state})")
    if snapshot.sopr is not None:
        state = "profit-taking pressure" if snapshot.sopr >= SOPR_HOT else "neutral"
        notes.append(f"SOPR {snapshot.sopr:.2f} ({state})")
    if snapshot.is_demo:
        notes.append("on-chain data is simulated — connect Glassnode/Whale-Alert for live data")
    if not notes:
        notes.append("on-chain flows broadly neutral")

    return OnChainResult(
        score=round(clamp(points), 1),
        whale_activity=round(snapshot.whale_activity, 1),
        exchange_netflow=round(snapshot.exchange_netflow, 1),
        active_addresses=round(snapshot.active_addresses, 1),
        mvrv=round(snapshot.mvrv, 2) if snapshot.mvrv is not None else None,
        sopr=round(snapshot.sopr, 3) if snapshot.sopr is not None else None,
        is_demo=snapshot.is_demo,
        notes=tuple(notes),
    )