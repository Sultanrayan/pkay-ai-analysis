"""Volume Analysis Agent.

Scores the latest volume picture from On-Balance Volume (OBV) direction and
how the most recent candle's volume compares to its 20-period average.
Rising OBV with above-average volume confirms a move; falling OBV with weak
volume questions it.
"""

from __future__ import annotations

from ..domain import Candle
from ..indicators import clamp, sma_series
from .base import VolumeResult

#: OBV trend window (candles) used to estimate the slope.
TREND_WINDOW = 20
#: Volume ratio at/above which the latest bar is treated as a confirmation.
HOT_VOLUME_RATIO = 1.2
#: Volume ratio at/below which the latest bar is treated as unconvincing.
COLD_VOLUME_RATIO = 0.8


def _obv(closes: list[float], volumes: list[float]) -> list[float]:
    """Cumulative On-Balance Volume (OBV)."""
    obv: list[float] = []
    running = 0.0
    for i, close in enumerate(closes):
        if i > 0:
            if close > closes[i - 1]:
                running += volumes[i]
            elif close < closes[i - 1]:
                running -= volumes[i]
        obv.append(running)
    return obv


def analyze(candles: list[Candle]) -> VolumeResult:
    """Score the volume confirmation of the latest candles."""
    if len(candles) < TREND_WINDOW + 1:
        raise ValueError(f"Volume analysis needs at least {TREND_WINDOW + 1} candles")

    closes = [c.close for c in candles]
    volumes = [c.volume for c in candles]
    obv = _obv(closes, volumes)

    # Normalized OBV slope over the window: net OBV change vs total volume.
    obv_change = obv[-1] - obv[-TREND_WINDOW]
    total_volume = sum(volumes[-TREND_WINDOW:])
    obv_slope = obv_change / total_volume if total_volume > 0 else 0.0
    obv_slope = clamp(obv_slope, -1.0, 1.0)

    volume_avg = sma_series(volumes, period=TREND_WINDOW)[-1]
    volume_ratio = volumes[-1] / volume_avg if volume_avg and volume_avg > 0 else 1.0

    notes: list[str] = []
    points = 0.0
    # OBV direction: confirmation of price trend.
    points += obv_slope * 60.0
    if obv_slope > 0.05:
        notes.append("OBV rising — volume supports the move")
    elif obv_slope < -0.05:
        notes.append("OBV falling — volume contradicts the move")

    # Latest-bar volume surge/drought.
    if volume_ratio >= HOT_VOLUME_RATIO:
        points += 40.0
        notes.append(f"volume {volume_ratio:.2f}x average — high participation")
    elif volume_ratio <= COLD_VOLUME_RATIO:
        points -= 40.0
        notes.append(f"volume {volume_ratio:.2f}x average — low participation")

    if not notes:
        notes.append("volume in line with the recent average")

    return VolumeResult(
        score=round(clamp(points), 1),
        obv_slope=round(obv_slope, 3),
        volume_ratio=round(volume_ratio, 2),
        notes=tuple(notes),
    )