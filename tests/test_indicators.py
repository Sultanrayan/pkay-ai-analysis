"""Unit tests for the pure indicator math."""

from __future__ import annotations

import math

import pytest
from conftest import make_candles

from tradingbot.domain import Timeframe
from tradingbot.indicators import (
    aggregate_candles,
    atr_series,
    correlation,
    ema_series,
    log_returns,
    macd_series,
    rolling_max,
    rolling_min,
    rsi_series,
    sma_series,
)

CONSTANT = [10.0] * 40


def test_sma_constant_series_is_constant():
    out = sma_series(CONSTANT, period=5)
    assert out[:4] == [None] * 4
    assert out[4:] == [10.0] * 36


def test_sma_matches_naive_mean():
    values = [float(i) for i in range(1, 31)]
    out = sma_series(values, period=3)
    assert out[2] == pytest.approx(2.0)   # mean(1, 2, 3)
    assert out[3] == pytest.approx(3.0)   # mean(2, 3, 4)
    assert out[29] == pytest.approx(29.0)  # mean(28, 29, 30)


def test_sma_too_short_returns_none():
    assert sma_series([1.0, 2.0], period=5) == [None, None]


def test_ema_weights_recent_values_more():
    rising = [float(i) for i in range(1, 51)]
    falling = list(reversed(rising))
    fast_rising = ema_series(rising, period=5)[-1]
    fast_falling = ema_series(falling, period=5)[-1]
    assert fast_rising is not None and fast_falling is not None
    assert fast_rising > fast_falling


def test_rsi_extremes():
    # All gains -> RSI 100; all losses -> RSI 0.
    gains = [1.0] + [2.0] * 20
    losses = [20.0 - i for i in range(20)]
    assert rsi_series(gains, period=14)[-1] == pytest.approx(100.0)
    assert rsi_series(losses, period=14)[-1] == pytest.approx(0.0)


def test_rsi_bounds_and_warmup():
    values = [math.sin(i / 3) + i * 0.01 for i in range(100)]
    out = rsi_series(values, period=14)
    assert out[:14] == [None] * 14
    valid = [v for v in out if v is not None]
    assert all(0.0 <= v <= 100.0 for v in valid)


def test_macd_histogram_sign_follows_momentum():
    rising = [float(i) for i in range(1, 80)]
    _, _, hist = macd_series(rising)
    assert hist[-1] is not None and hist[-1] > 0
    falling = list(reversed(rising))
    _, _, hist_falling = macd_series(falling)
    assert hist_falling[-1] is not None and hist_falling[-1] < 0


def test_atr_positive_and_grows_with_range():
    calm = make_candles(30)
    wild = make_candles(30)
    # Widen the wild range artificially on the last third of candles.
    widened = [
        c.__class__(
            open_time=c.open_time, open=c.open, high=c.high * 5, low=c.low / 5,
            close=c.close, volume=c.volume,
        ) if i > 15 else c
        for i, c in enumerate(wild)
    ]
    calm_atr = atr_series(calm, period=14)[-1]
    wild_atr = atr_series(widened, period=14)[-1]
    assert calm_atr is not None and calm_atr > 0
    assert wild_atr is not None and wild_atr > calm_atr


def test_rolling_min_max():
    values = [3.0, 1.0, 4.0, 1.5, 2.0]
    assert rolling_min(values, period=3) == [None, None, 1.0, 1.0, 1.5]
    assert rolling_max(values, period=3) == [None, None, 4.0, 4.0, 4.0]


def test_log_returns_first_is_none_and_positive_for_growth():
    out = log_returns([100.0, 110.0, 121.0])
    assert out[0] is None
    assert out[1] == pytest.approx(math.log(1.1))
    assert out[2] == pytest.approx(math.log(1.1))


def test_correlation_identical_is_one():
    a = [1.0 + i * 0.1 for i in range(50)]
    assert correlation(a, a) == pytest.approx(1.0)


def test_correlation_inverse_is_minus_one():
    a = [float(i) for i in range(1, 51)]
    b = [float(i) for i in range(50, 0, -1)]
    assert correlation(a, b) == pytest.approx(-1.0)


def test_correlation_none_for_short_or_flat():
    assert correlation([1.0], [2.0]) is None
    assert correlation([1.0] * 10, [1.0] * 10) is None


def test_correlation_skips_none_gaps():
    a = [1.0, 2.0, None, 3.0, 4.0]
    b = [1.0, 2.0, 9.9, 3.0, 4.0]
    assert correlation(a, b) == pytest.approx(1.0)


def test_aggregate_candles_builds_ohlc():
    hourlies = make_candles(count=8, step_seconds=3600)
    dailies = aggregate_candles(hourlies, Timeframe.D1)
    assert len(dailies) == 1
    day = dailies[0]
    assert day.open == hourlies[0].open
    assert day.close == hourlies[-1].close
    assert day.high == max(c.high for c in hourlies)
    assert day.low == min(c.low for c in hourlies)
    assert day.volume == pytest.approx(sum(c.volume for c in hourlies))


def test_aggregate_candles_hour_boundaries():
    # 90 minute candles -> exactly one 2h bucket (two buckets if misaligned).
    candles = make_candles(count=2, step_seconds=5400)
    two_hour = aggregate_candles(candles, Timeframe.H4)
    assert len(two_hour) == 1
