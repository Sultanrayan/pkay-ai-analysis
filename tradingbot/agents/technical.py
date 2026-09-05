"""Technical Analysis Agent.

Computes a directional score in -100..+100 from moving-average trend,
MACD momentum and RSI conditions over the latest candle series.

Scoring is deliberately transparent — a weighted sum of bounded components —
so the signal can be explained (and unit tested) component by component:

* close vs SMA(50)            +/-25
* SMA(50) vs SMA(200)         +/-25
* MACD histogram sign         +/-30
* RSI above/below 50          +/-20
* RSI extreme mean-reversion  +/-10 (overbought > 75 / oversold < 25)
"""

from __future__ import annotations

from ..domain import Candle
from ..indicators import clamp, macd_series, rolling_max, rolling_min, rsi_series, sma_series
from .base import TechnicalResult

#: Minimum candles required for a meaningful MA-200/RIS read.
MIN_CANDLES = 60

_OVERBOUGHT = 75.0
_OVERSOLD = 25.0


def analyze(candles: list[Candle]) -> TechnicalResult:
    """Score the latest technical setup of ``candles`` (oldest first)."""
    if len(candles) < MIN_CANDLES:
        raise ValueError(
            f"Technical analysis needs at least {MIN_CANDLES} candles, got {len(candles)}"
        )

    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    current = closes[-1]

    rsi = rsi_series(closes, period=14)[-1]
    ma_50 = sma_series(closes, period=50)[-1]
    ma_200 = sma_series(closes, period=200)[-1]
    macd, signal_line, histogram = macd_series(closes)
    macd_last = macd[-1]
    signal_last = signal_line[-1]
    hist_last = histogram[-1]
    support = rolling_min(lows, period=20)[-1]
    resistance = rolling_max(highs, period=20)[-1]

    points = 0.0
    notes: list[str] = []

    if ma_50 is not None:
        if current > ma_50:
            points += 25.0
        else:
            points -= 25.0
    if ma_50 is not None and ma_200 is not None:
        if ma_50 > ma_200:
            points += 25.0
            notes.append("golden alignment: MA50 above MA200")
        else:
            points -= 25.0
            notes.append("death alignment: MA50 below MA200")
    elif ma_200 is None:
        notes.append("MA200 unavailable on this window")

    if hist_last is not None:
        if hist_last >= 0:
            points += 30.0
            notes.append("MACD histogram positive")
        else:
            points -= 30.0
            notes.append("MACD histogram negative")

    if rsi is not None:
        if rsi > _OVERBOUGHT:
            points += 10.0 - 20.0  # bullish side but overbought penalty
            notes.append(f"RSI {rsi:.1f} overbought (mean-reversion risk)")
        elif rsi < _OVERSOLD:
            points -= 10.0 + 20.0  # bearish side but oversold bounce potential
            notes.append(f"RSI {rsi:.1f} oversold (bounce potential)")
        elif rsi >= 50.0:
            points += 20.0
            notes.append(f"RSI {rsi:.1f} above 50 (bullish momentum)")
        else:
            points -= 20.0
            notes.append(f"RSI {rsi:.1f} below 50 (bearish momentum)")

    score = round(clamp(points), 1)
    momentum = "bullish" if score >= 25.0 else "bearish" if score <= -25.0 else "neutral"

    if not notes:
        notes.append("no dominant trend structure detected")

    return TechnicalResult(
        score=score,
        rsi=round(rsi, 2) if rsi is not None else None,
        macd=round(macd_last, 6) if macd_last is not None else None,
        macd_signal=round(signal_last, 6) if signal_last is not None else None,
        macd_histogram=round(hist_last, 6) if hist_last is not None else None,
        ma_50=round(ma_50, 2) if ma_50 is not None else None,
        ma_200=round(ma_200, 2) if ma_200 is not None else None,
        support=round(support, 2) if support is not None else None,
        resistance=round(resistance, 2) if resistance is not None else None,
        momentum=momentum,
        notes=tuple(notes),
    )
