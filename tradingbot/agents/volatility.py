"""Volatility Analysis Agent.

Measures the volatility regime from Bollinger Bands (SMA-20 +/- 2 sigma):

* ``band_position`` — where price sits inside the bands (-1 lower .. +1 upper);
  pressing the upper band with momentum reads bullish, the lower band bearish.
* ``squeeze`` — bands unusually tight, which historically precedes expansion
  (noted for context; direction stays unknown until it resolves).
* Extreme ATR volatility is penalized as a poor setup.

Deliberately complements the risk agent: risk sizes the trade, this agent
describes the regime for the technical consensus.
"""

from __future__ import annotations

import math

from ..domain import Candle
from ..indicators import atr_series, clamp, sma_series, std_series
from .base import VolatilityResult

BB_PERIOD = 20
BB_MULT = 2.0
#: Band width (as % of middle) below this fraction of its 20-bar average is a squeeze.
SQUEEZE_RATIO = 0.5
#: ATR above this % of price counts as an extreme regime.
EXTREME_ATR_PCT = 4.0


def analyze(candles: list[Candle]) -> VolatilityResult:
    """Score the volatility regime of the latest candle."""
    if len(candles) < BB_PERIOD * 2:
        raise ValueError(f"Volatility analysis needs at least {BB_PERIOD * 2} candles")

    closes = [c.close for c in candles]
    last = candles[-1]

    middle = sma_series(closes, BB_PERIOD)[-1]
    deviation = std_series(closes, BB_PERIOD)[-1]
    if middle is None or deviation is None or deviation <= 0:
        raise ValueError("Bollinger bands unavailable — cannot score volatility")
    upper = middle + BB_MULT * deviation
    lower = middle - BB_MULT * deviation

    band_width = upper - lower
    band_width_pct = band_width / middle * 100.0 if middle else 0.0

    # Position of the close inside the bands: -1 at the lower band, +1 at upper.
    band_position = clamp((last.close - middle) / (band_width / 2.0), -1.0, 1.0)

    # Squeeze: current width below half of its recent average width.
    widths: list[float] = []
    for i in range(BB_PERIOD, len(candles)):
        window = closes[i - BB_PERIOD + 1 : i + 1]
        m = sum(window) / BB_PERIOD
        variance = sum((v - m) ** 2 for v in window) / BB_PERIOD
        d = math.sqrt(variance)
        if d > 0:
            widths.append((m + BB_MULT * d - (m - BB_MULT * d)) / m * 100.0)
    avg_width = sum(widths[-BB_PERIOD:]) / BB_PERIOD if len(widths) >= BB_PERIOD else 0.0
    squeeze = avg_width > 0 and band_width_pct < avg_width * SQUEEZE_RATIO

    atr_value = atr_series(candles, period=14)[-1]
    atr_pct = (atr_value / last.close * 100.0) if atr_value else 0.0

    notes: list[str] = []
    points = band_position * 60.0
    if band_position >= 0.5:
        notes.append("price pressing the upper band — momentum bullish")
    elif band_position <= -0.5:
        notes.append("price at the lower band — momentum bearish")
    else:
        notes.append("price mid-band — no strong volatility signal")
    if squeeze:
        notes.append("band squeeze — expansion imminent, direction unresolved")
    if atr_pct >= EXTREME_ATR_PCT:
        points -= 25.0
        notes.append(f"extreme volatility ({atr_pct:.1f}%/candle)")

    return VolatilityResult(
        score=round(clamp(points), 1),
        atr_pct=round(atr_pct, 2),
        band_width_pct=round(band_width_pct, 2),
        band_position=round(band_position, 2),
        squeeze=squeeze,
        notes=tuple(notes),
    )