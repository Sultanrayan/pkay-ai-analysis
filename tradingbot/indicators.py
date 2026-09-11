"""Deterministic technical indicator math.

Pure functions over plain Python floats — deliberately dependency-free so
the hot path (a few hundred candles per analysis) stays fast, portable and
easy to unit test. Every *series* function returns a list aligned with the
input where entries before the warm-up period are ``None``.

Each function is documented with its formula so behaviour can be audited or
replaced with a heavier library (pandas / TA-Lib) later without callers
changing.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from .domain import Candle, Timeframe

Number = float | None


def clamp(value: float, low: float = -100.0, high: float = 100.0) -> float:
    """Clamp ``value`` into the inclusive ``[low, high]`` range."""
    return max(low, min(high, value))


def sma_series(values: Sequence[float], period: int) -> list[Number]:
    """Simple moving average: mean of the last ``period`` values.

    Warm-up: ``None`` for the first ``period - 1`` indices.
    """
    if period <= 0 or len(values) < period:
        return [None] * len(values)
    out: list[Number] = [None] * (period - 1)
    window_sum = sum(values[:period])
    out.append(window_sum / period)
    for i in range(period, len(values)):
        window_sum += values[i] - values[i - period]
        out.append(window_sum / period)
    return out


def ema_series(values: Sequence[float], period: int) -> list[Number]:
    """Exponential moving average with smoothing factor ``2 / (period + 1)``.

    Seeded with the first value; the first few samples are warm-up biased,
    which is acceptable for the look-back lengths used here.
    """
    if period <= 0 or not values:
        return [None] * len(values)
    alpha = 2.0 / (period + 1.0)
    out: list[Number] = []
    previous = values[0]
    for i, value in enumerate(values):
        previous = value if i == 0 else alpha * value + (1.0 - alpha) * previous
        out.append(previous)
    return out


def std_series(values: Sequence[float], period: int = 20) -> list[Number]:
    """Rolling population standard deviation (``None`` during warm-up)."""
    n = len(values)
    out: list[Number] = [None] * n
    if n < period:
        return out
    window: list[float] = []
    for i, value in enumerate(values):
        window.append(value)
        if len(window) > period:
            window.pop(0)
        if len(window) == period:
            mean = sum(window) / period
            variance = sum((v - mean) ** 2 for v in window) / period
            out[i] = math.sqrt(variance)
    return out


def rsi_series(values: Sequence[float], period: int = 14) -> list[Number]:
    """Relative Strength Index (Wilder smoothing).

    First valid value at index ``period``. RSI is 100 when average losses are
    zero (no division by zero).
    """
    n = len(values)
    out: list[Number] = [None] * n
    if n < period + 1:
        return out

    avg_gain = avg_loss = 0.0
    for i in range(1, period + 1):
        change = values[i] - values[i - 1]
        avg_gain += max(change, 0.0)
        avg_loss += max(-change, 0.0)
    avg_gain /= period
    avg_loss /= period

    def rsi_value(gain: float, loss: float) -> float:
        if loss == 0.0:
            return 100.0
        return 100.0 - 100.0 / (1.0 + gain / loss)

    out[period] = rsi_value(avg_gain, avg_loss)
    for i in range(period + 1, n):
        change = values[i] - values[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(change, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-change, 0.0)) / period
        out[i] = rsi_value(avg_gain, avg_loss)
    return out


def macd_series(
    values: Sequence[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[list[Number], list[Number], list[Number]]:
    """MACD line, signal line and histogram (EMA fast - EMA slow).

    Returns three lists aligned with ``values``; warm-up bias is inherent to
    the EMA seeding above.
    """
    fast_ema = ema_series(values, fast)
    slow_ema = ema_series(values, slow)
    macd: list[Number] = []
    for f, s in zip(fast_ema, slow_ema, strict=True):
        macd.append(None if f is None or s is None else f - s)
    signal_ema = ema_series([v for v in macd if v is not None], signal)
    sig_iter = iter(signal_ema)
    histogram: list[Number] = []
    signal_line: list[Number] = []
    for m in macd:
        sig = next(sig_iter) if m is not None else None
        signal_line.append(sig)
        histogram.append(None if m is None or sig is None else m - sig)
    return macd, signal_line, histogram


def atr_series(candles: Sequence[Candle], period: int = 14) -> list[Number]:
    """Average True Range (Wilder smoothing).

    True range needs the previous close, so TR[0] = high - low. The first ATR
    is the mean of the first ``period`` true ranges (index ``period - 1``).
    """
    n = len(candles)
    out: list[Number] = [None] * n
    if n < period:
        return out

    true_ranges: list[float] = []
    for i, candle in enumerate(candles):
        if i == 0:
            tr = candle.high - candle.low
        else:
            prev_close = candles[i - 1].close
            tr = max(
                candle.high - candle.low,
                abs(candle.high - prev_close),
                abs(candle.low - prev_close),
            )
        true_ranges.append(tr)

    atr = sum(true_ranges[:period]) / period
    out[period - 1] = atr
    for i in range(period, n):
        atr = (atr * (period - 1) + true_ranges[i]) / period
        out[i] = atr
    return out


def rolling_max(values: Sequence[float], period: int) -> list[Number]:
    """Rolling maximum (``None`` before ``period - 1`` samples exist)."""
    if period <= 0:
        return [None] * len(values)
    out: list[Number] = [None] * min(period - 1, len(values))
    window: list[float] = []
    for value in values:
        window.append(value)
        if len(window) > period:
            window.pop(0)
        if len(window) == period:
            out.append(max(window))
    return out


def rolling_min(values: Sequence[float], period: int) -> list[Number]:
    """Rolling minimum (``None`` before ``period - 1`` samples exist)."""
    if period <= 0:
        return [None] * len(values)
    out: list[Number] = [None] * min(period - 1, len(values))
    window: list[float] = []
    for value in values:
        window.append(value)
        if len(window) > period:
            window.pop(0)
        if len(window) == period:
            out.append(min(window))
    return out


def log_returns(values: Sequence[float]) -> list[Number]:
    """Period-over-period log returns; first entry is ``None``."""
    out: list[Number] = [None]
    for i in range(1, len(values)):
        previous = values[i - 1]
        out.append(None if previous == 0 else math.log(values[i] / previous))
    return out


def correlation(series_a: Sequence[Number], series_b: Sequence[Number]) -> float | None:
    """Pearson correlation between two equally-long series of possibly-``None``
    values. Pass ``strict`` alignment: ``series_a`` and ``series_b`` must have
    the same length.

    Returns ``None`` when there are fewer than two usable paired samples or
    when either series has zero variance.
    """
    if len(series_a) != len(series_b):
        raise ValueError("correlation() requires equally long series")
    pairs: list[tuple[float, float]] = []
    for a, b in zip(series_a, series_b, strict=True):
        if a is not None and b is not None and math.isfinite(a) and math.isfinite(b):
            pairs.append((a, b))
    if len(pairs) < 2:
        return None
    mean_a = sum(a for a, _ in pairs) / len(pairs)
    mean_b = sum(b for _, b in pairs) / len(pairs)
    cov = 0.0
    var_a = 0.0
    var_b = 0.0
    for a, b in pairs:
        da = a - mean_a
        db = b - mean_b
        cov += da * db
        var_a += da * da
        var_b += db * db
    if var_a == 0.0 or var_b == 0.0:
        return None
    return cov / math.sqrt(var_a * var_b)


def aggregate_candles(candles: Iterable[Candle], timeframe: Timeframe) -> list[Candle]:
    """Resample candles into a coarser timeframe by bucketing open times.

    Buckets are aligned to UTC multiples of the target timeframe length. Each
    output candle keeps the first open/high, lowest low, last close and sums
    volume. Output is sorted by open time.
    """
    bucket_minutes = timeframe.minutes()
    buckets: dict[int, list[Candle]] = {}
    for candle in candles:
        key = candle.epoch() // (bucket_minutes * 60)
        buckets.setdefault(key, []).append(candle)

    merged: list[Candle] = []
    for key in sorted(buckets):
        group = buckets[key]
        merged.append(
            Candle(
                open_time=group[0].open_time,
                open=group[0].open,
                high=max(c.high for c in group),
                low=min(c.low for c in group),
                close=group[-1].close,
                volume=sum(c.volume for c in group),
            )
        )
    return merged
