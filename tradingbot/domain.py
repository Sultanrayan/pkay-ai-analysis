"""Shared domain models.

Enums and plain dataclasses that travel between the data layer, the agents,
the analysis runner and the storage layer. Keeping them here (and free of
I/O) avoids circular imports and keeps every module focused on one job.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class Symbol(str, Enum):
    """Trading pairs the bot can analyze."""

    BTCUSD = "BTCUSD"
    XAUUSD = "XAUUSD"

    @classmethod
    def parse(cls, raw: str) -> Symbol | None:
        """Case-insensitive parse of a user supplied symbol string."""
        normalized = raw.strip().upper().replace("/", "").replace("_", "")
        if normalized == "BTCUSDT":
            normalized = "BTCUSD"
        try:
            return cls(normalized)
        except ValueError:
            return None

    def counterpart(self) -> Symbol:
        """The other asset in the pair (BTCUSD <-> XAUUSD)."""
        return Symbol.XAUUSD if self is Symbol.BTCUSD else Symbol.BTCUSD


class Timeframe(str, Enum):
    """Supported chart timeframes (values double as Binance interval names)."""

    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"

    def minutes(self) -> int:
        """Length of one candle in minutes (used for resampling)."""
        return {"1h": 60, "4h": 240, "1d": 1440, "1w": 10080}[self.value]

    @classmethod
    def parse(cls, raw: str) -> Timeframe | None:
        normalized = raw.strip().lower()
        try:
            return cls(normalized)
        except ValueError:
            return None


class Signal(str, Enum):
    """Trading signal produced by the decision engine."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


def utcnow() -> datetime:
    """Timezone-aware UTC now (single helper so tests can patch it)."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class Candle:
    """One OHLCV candle. ``open_time`` is timezone-aware UTC."""

    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def epoch(self) -> int:
        return int(self.open_time.timestamp())


@dataclass(frozen=True, slots=True)
class NewsItem:
    """A single news headline used for sentiment scoring."""

    title: str
    url: str = ""
    source: str = ""


@dataclass(frozen=True, slots=True)
class SentimentSnapshot:
    """Aggregated, symbol-scoped sentiment inputs for the sentiment agent.

    ``overall_score`` ranges -100 (very bearish) to +100 (very bullish).
    ``is_demo`` marks fallback/deterministic data so reports can disclose it.
    """

    news_score: float  # -100..+100 from headline scoring
    news_count: int
    headlines: tuple[NewsItem, ...]
    fear_greed_value: float  # 0..100
    fear_greed_label: str
    social_volume: int
    overall_score: float  # -100..+100
    sources: tuple[str, ...]
    is_demo: bool = False


# Convenience aliases used across the code base.
Candles = list[Candle]
