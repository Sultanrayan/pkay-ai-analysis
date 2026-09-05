"""Pytest bootstrap: make the project root importable regardless of how
pytest is invoked, and share reusable fixtures/helpers."""

from __future__ import annotations

import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from tradingbot.domain import Candle  # noqa: E402


def make_candles(
    count: int = 300,
    start_price: float = 100.0,
    drift_per_step: float = 0.0,
    step_seconds: int = 3600,
    seed_time: datetime | None = None,
) -> list[Candle]:
    """Deterministic OHLCV series ending at a known timestamp.

    Prices evolve as ``close = previous * (1 + drift + sin(i/9) * 0.01)`` —
    a stable, wavy series that exercises indicator code without randomness.
    """
    base_time = seed_time or datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles: list[Candle] = []
    price = start_price
    for i in range(count):
        open_time = base_time + timedelta(seconds=i * step_seconds)
        wave = math.sin(i / 9.0) * 0.01
        close = price * (1.0 + drift_per_step + wave)
        high = max(price, close) * 1.004
        low = min(price, close) * 0.996
        candles.append(
            Candle(
                open_time=open_time,
                open=price,
                high=high,
                low=low,
                close=close,
                volume=1000.0 + i,
            )
        )
        price = close
    return candles


@pytest.fixture
def candles() -> list[Candle]:
    return make_candles()


@pytest.fixture
def trending_up_candles() -> list[Candle]:
    return make_candles(count=300, start_price=50.0, drift_per_step=0.004)
