"""Pattern Recognition Agent.

Looks for short-horizon breakout/mean-reversion structure:

* A close above the prior 20-bar high is a bullish breakout; below the prior
  20-bar low a bearish one.
* Otherwise price is scored by where it sits between the 20-bar support and
  resistance levels (proximity), which describes mean-reversion context.

Pure function over candles; the technical agent owns the longer-horizon
trend, this one only the local price structure.
"""

from __future__ import annotations

from ..domain import Candle
from ..indicators import clamp, rolling_max, rolling_min
from .base import PatternResult

LOOKBACK = 20


def analyze(candles: list[Candle]) -> PatternResult:
    """Score the local price pattern of the latest candle."""
    if len(candles) < LOOKBACK + 1:
        raise ValueError(f"Pattern analysis needs at least {LOOKBACK + 1} candles")

    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    current = candles[-1].close

    # Levels from the trailing window *excluding* the latest bar so a close
    # beyond them genuinely counts as a breakout.
    support_prev = rolling_min(lows[:-1], period=LOOKBACK)[-1]
    resistance_prev = rolling_max(highs[:-1], period=LOOKBACK)[-1]
    support = rolling_min(lows, period=LOOKBACK)[-1]
    resistance = rolling_max(highs, period=LOOKBACK)[-1]

    notes: list[str] = []
    breakout = "none"
    proximity = 0.0
    points = 0.0

    if resistance_prev is not None and current > resistance_prev:
        breakout = "bullish"
        points += 60.0
        notes.append(f"close above {LOOKBACK}-bar resistance — bullish breakout")
    elif support_prev is not None and current < support_prev:
        breakout = "bearish"
        points -= 60.0
        notes.append(f"close below {LOOKBACK}-bar support — bearish breakdown")
    elif support is not None and resistance is not None and resistance > support:
        proximity = clamp((current - support) / (resistance - support) * 2.0 - 1.0, -1.0, 1.0)
        points += proximity * 40.0
        if proximity >= 0.5:
            notes.append("price testing resistance — watch for a breakout")
        elif proximity <= -0.5:
            notes.append("price near support — watch for a bounce")
        else:
            notes.append("price range-bound between support and resistance")

    if not notes:
        notes.append("no clear local pattern detected")

    return PatternResult(
        score=round(clamp(points), 1),
        breakout=breakout,
        support=round(support, 2) if support is not None else None,
        resistance=round(resistance, 2) if resistance is not None else None,
        proximity=round(proximity, 2),
        notes=tuple(notes),
    )