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
    """Trading pairs the bot can analyze (V3: multi-asset)."""

    BTCUSDT = "BTCUSDT"
    ETHUSDT = "ETHUSDT"
    SOLUSDT = "SOLUSDT"
    XAUUSD = "XAUUSD"

    @classmethod
    def parse(cls, raw: str) -> Symbol | None:
        """Case-insensitive parse of a user supplied symbol string.

        Accepts common exchange spellings (``BTCUSD``, ``BTC-USD``,
        ``btc/usdt``) and normalizes them to the canonical market name.
        """
        normalized = raw.strip().upper().replace("/", "").replace("_", "").replace("-", "")
        if normalized == "BTCUSD":
            normalized = "BTCUSDT"
        try:
            return cls(normalized)
        except ValueError:
            return None

    def correlation_peer(self) -> Symbol:
        """The asset correlated against for diversification context.

        Crypto majors pair with gold; the two altcoins pair with each other
        (the classic BTC↔XAU and ETH↔SOL cross-asset relationships).
        """
        return {
            Symbol.BTCUSDT: Symbol.XAUUSD,
            Symbol.XAUUSD: Symbol.BTCUSDT,
            Symbol.ETHUSDT: Symbol.SOLUSDT,
            Symbol.SOLUSDT: Symbol.ETHUSDT,
        }[self]


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


@dataclass(frozen=True, slots=True)
class OnChainSnapshot:
    """Symbol-scoped on-chain inputs for the on-chain agent.

    Without a paid provider key the data manager serves deterministic
    heuristic values flagged with ``is_demo=True``; the agent itself is a
    pure function so a live Glassnode/Whale-Alert feed can be plugged in
    behind the same snapshot without touching the agent.
    """

    whale_activity: float  # -100..+100, positive = accumulation
    exchange_netflow: float  # -100..+100, positive = exchange outflows (bullish)
    active_addresses: float  # -100..+100 trend
    mvrv: float | None  # Market-Value-to-Realized-Value ratio
    sopr: float | None  # Spent Output Profit Ratio
    is_demo: bool = False


@dataclass(frozen=True, slots=True)
class MacroSnapshot:
    """Macro-economic inputs for the macro agent (heuristic/demo by default).

    Each trend is -1 (bearish for risk assets) .. +1 (bullish for risk
    assets): easing rates, a weaker dollar and disinflation all read as +1.
    """

    rate_trend: float  # +1 = central banks easing
    dxy_trend: float  # +1 = dollar weakening
    inflation_trend: float  # +1 = disinflation
    is_demo: bool = False


@dataclass(frozen=True, slots=True)
class SniperToken:
    """One candidate token from a signal-only sniper scan.

    The sniper is deliberately **detection only** — it reports opportunities
    and their risk profile and never places an order.
    """

    symbol: str
    chain: str
    liquidity_usd: float
    volume_5m_usd: float
    hype_score: float  # 0..100
    safety_score: float  # 0..100 (higher = safer: locked liquidity, audits...)
    launch_age_minutes: int
    price_change_pct: float
    risks: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SniperScan:
    """Result of a memecoin scan (demo scanner unless a live feed is wired)."""

    tokens: tuple[SniperToken, ...] = ()
    source: str = "demo"
    is_demo: bool = True


# Convenience aliases used across the code base.
Candles = list[Candle]