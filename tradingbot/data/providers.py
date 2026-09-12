"""Market data providers.

Every provider implements :class:`CandleProvider` so the data manager can
treat them uniformly and try them in order (primary live API first, demo last
as an offline fallback). HTTP parsing lives in module-level pure functions
(``parse_*``) so it can be unit tested without network access.
"""

from __future__ import annotations

import logging
import math
import random
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, Protocol

import httpx

from ..domain import Candle, Symbol, Timeframe, utcnow

logger = logging.getLogger(__name__)

#: Maximum candles requested from any provider. Enough for a MA-200 and RSI
#: warm-up while keeping responses small.
DEFAULT_LIMIT = 500

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

PRICE_BASE: dict[Symbol, float] = {
    Symbol.BTCUSDT: 64_000.0,
    Symbol.ETHUSDT: 3_200.0,
    Symbol.SOLUSDT: 150.0,
    Symbol.XAUUSD: 2_350.0,
}


class ProviderError(Exception):
    """Raised when a provider cannot serve data for a request.

    The data manager catches this and moves on to the next provider in the
    chain, so it is deliberately not a fatal error.
    """


class CandleProvider(Protocol):
    """A source of OHLCV candles."""

    #: Human readable provider name shown in reports/logs.
    name: str
    #: Whether the data is deterministic demo data.
    is_demo: bool = False

    def supports(self, symbol: Symbol) -> bool: ...

    async def fetch_candles(
        self, symbol: Symbol, timeframe: Timeframe, limit: int = DEFAULT_LIMIT
    ) -> list[Candle]: ...


def _to_utc(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def parse_binance_klines(payload: Sequence[Sequence[Any]]) -> list[Candle]:
    """Parse a Binance ``/api/v3/klines`` response into candles.

    Binance kline layout (documented): ``[openTime, open, high, low, close,
    volume, closeTime, ...]`` with prices/volume as strings.
    """
    candles: list[Candle] = []
    for row in payload:
        try:
            candles.append(
                Candle(
                    open_time=_to_utc(int(row[0]) / 1000.0),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                )
            )
        except (IndexError, TypeError, ValueError) as exc:
            raise ProviderError(f"Malformed Binance kline row: {row!r}") from exc
    if not candles:
        raise ProviderError("Binance returned no candles")
    return candles


def parse_yahoo_chart(payload: dict[str, Any]) -> list[Candle]:
    """Parse a Yahoo Finance chart API response into candles.

    Response shape: ``{"chart": {"result": [{"timestamp": [...], "indicators":
    {"quote": [{"open": [...], "high": [...], ...}]}}]}}``. Any of the OHLC
    arrays may contain ``null`` gaps which are skipped.
    """
    try:
        result = payload["chart"]["result"][0]
        timestamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError("Yahoo response missing chart data") from exc

    candles: list[Candle] = []
    for i, ts in enumerate(timestamps):
        try:
            open_ = quote["open"][i]
            high = quote["high"][i]
            low = quote["low"][i]
            close = quote["close"][i]
            volume = quote["volume"][i]
        except (KeyError, IndexError, TypeError):
            continue
        # Yahoo uses null placeholders for suspended/no-trade slots.
        if None in (open_, high, low, close):
            continue
        try:
            candles.append(
                Candle(
                    open_time=_to_utc(int(ts)),
                    open=float(open_),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    volume=float(volume or 0.0),
                )
            )
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"Malformed Yahoo bar at index {i}") from exc
    if not candles:
        raise ProviderError("Yahoo returned no candles")
    return candles


# --------------------------------------------------------------------------
# Live providers
# --------------------------------------------------------------------------

class BinanceProvider:
    """Public Binance REST API (no keys needed) for the crypto majors.

    ``BTCUSDT``/``ETHUSDT``/``SOLUSDT`` map 1:1 to Binance spot markets;
    gold (``XAUUSD``) is served by the Yahoo provider instead.
    """

    name = "binance"
    is_demo = False
    BASE_URL = "https://api.binance.com/api/v3/klines"
    _MARKETS: dict[Symbol, str] = {
        Symbol.BTCUSDT: "BTCUSDT",
        Symbol.ETHUSDT: "ETHUSDT",
        Symbol.SOLUSDT: "SOLUSDT",
    }

    def __init__(self, client: httpx.AsyncClient, timeout: float = 10.0) -> None:
        self._client = client
        self._timeout = timeout

    def supports(self, symbol: Symbol) -> bool:
        return symbol in self._MARKETS

    async def fetch_candles(
        self, symbol: Symbol, timeframe: Timeframe, limit: int = DEFAULT_LIMIT
    ) -> list[Candle]:
        if not self.supports(symbol):
            raise ProviderError(f"Binance does not provide {symbol.value}")
        params = {
            "symbol": self._MARKETS[symbol],
            "interval": timeframe.value,
            "limit": str(limit),
        }
        try:
            response = await self._client.get(
                self.BASE_URL, params=params, timeout=self._timeout, follow_redirects=True
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Binance request failed: {exc}") from exc
        return parse_binance_klines(response.json())


class YahooProvider:
    """Keyless Yahoo Finance chart API.

    Symbol routing (public/spot-vs-futures realities):
      * ``BTCUSDT`` -> ``BTC-USD`` (crypto pair; fallback when Binance is down)
      * ``ETHUSDT`` -> ``ETH-USD``
      * ``SOLUSDT`` -> ``SOL-USD``
      * ``XAUUSD``  -> ``GC=F``    (COMEX gold futures, a liquid proxy for
        spot gold since keyless spot gold feeds are not available)

    Yahoo does not expose 4h/1w intervals natively, so 4h candles are
    aggregated from 1h and 1w candles from the weekly interval where
    available; a fine-grained fetch + :func:`aggregate_candles` fallback keeps
    behaviour predictable.
    """

    name = "yahoo"
    is_demo = False
    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
    _TICKERS: dict[Symbol, str] = {
        Symbol.BTCUSDT: "BTC-USD",
        Symbol.ETHUSDT: "ETH-USD",
        Symbol.SOLUSDT: "SOL-USD",
        Symbol.XAUUSD: "GC=F",
    }
    #: (interval, range) per timeframe. Aggregated timeframes use 60m.
    _INTERVALS: dict[Timeframe, tuple[str, str]] = {
        Timeframe.M1: ("1m", "7d"),
        Timeframe.M5: ("5m", "60d"),
        Timeframe.M15: ("15m", "60d"),
        Timeframe.H1: ("60m", "10d"),
        Timeframe.H4: ("60m", "60d"),
        Timeframe.D1: ("1d", "2y"),
        Timeframe.W1: ("1wk", "5y"),
    }

    def __init__(self, client: httpx.AsyncClient, timeout: float = 10.0) -> None:
        self._client = client
        self._timeout = timeout

    def supports(self, symbol: Symbol) -> bool:
        return symbol in self._TICKERS

    async def fetch_candles(
        self, symbol: Symbol, timeframe: Timeframe, limit: int = DEFAULT_LIMIT
    ) -> list[Candle]:
        if not self.supports(symbol):
            raise ProviderError(f"Yahoo does not provide {symbol.value}")
        interval, range_ = self._INTERVALS[timeframe]
        params = {"interval": interval, "range": range_, "includePrePost": "false"}
        url = f"{self.BASE_URL}/{self._TICKERS[symbol]}"
        try:
            response = await self._client.get(
                url,
                params=params,
                headers=DEFAULT_HEADERS,
                timeout=self._timeout,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Yahoo request failed: {exc}") from exc
        candles = parse_yahoo_chart(response.json())
        if timeframe in (Timeframe.H4,):
            from ..indicators import aggregate_candles

            candles = aggregate_candles(candles, timeframe)
        candles = candles[-limit:]
        if len(candles) < 2:
            raise ProviderError("Yahoo returned too few candles")
        return candles


# --------------------------------------------------------------------------
# Deterministic demo provider (offline development / fallback)
# --------------------------------------------------------------------------

class DemoProvider:
    """Deterministic, offline candle generator.

    Generates a pseudo random walk with a slow cyclical drift seeded by
    ``symbol + timeframe`` so repeated calls return identical series (which
    keeps tests and screenshots stable). Clearly flagged via ``is_demo`` so
    reports can disclose that the data is simulated.
    """

    name = "demo"
    is_demo = True

    def supports(self, symbol: Symbol) -> bool:
        return symbol in PRICE_BASE

    async def fetch_candles(
        self, symbol: Symbol, timeframe: Timeframe, limit: int = DEFAULT_LIMIT
    ) -> list[Candle]:
        base = PRICE_BASE[symbol]
        seed = f"{symbol.value}:{timeframe.value}"
        rng = random.Random(seed)
        phase = rng.uniform(0, math.tau)

        step_minutes = timeframe.minutes()
        now = utcnow()
        bucket = int(now.timestamp()) // (step_minutes * 60)
        end_epoch = bucket * step_minutes * 60

        # Walk backwards so the newest candle always ends at the latest
        # aligned boundary; then reverse for chronological order.
        candles: list[Candle] = []
        price = base * rng.uniform(0.94, 1.06)
        for i in range(limit):
            epoch = end_epoch - (limit - 1 - i) * step_minutes * 60
            t = i / 24.0  # ~one cycle per day for 1h candles
            drift = 0.0006 * math.sin(t / 4.0 + phase) + 0.0002 * math.sin(t / 0.7)
            change = drift + rng.gauss(0.0, 0.004)
            open_ = price
            close = max(open_ * (1.0 + change), 0.01)
            high = max(open_, close) * (1.0 + abs(rng.gauss(0.0, 0.0025)))
            low = min(open_, close) * (1.0 - abs(rng.gauss(0.0, 0.0025)))
            volume = base * (0.02 + 0.06 * rng.random())
            candles.append(
                Candle(
                    open_time=_to_utc(epoch),
                    open=round(open_, 6),
                    high=round(high, 6),
                    low=round(low, 6),
                    close=round(close, 6),
                    volume=round(volume, 2),
                )
            )
            price = close
        return candles


def candle_to_dict(candle: Candle) -> dict[str, Any]:
    """Serialize a candle for the JSON cache."""
    return {
        "open_time": candle.epoch(),
        "open": candle.open,
        "high": candle.high,
        "low": candle.low,
        "close": candle.close,
        "volume": candle.volume,
    }


def candles_from_dicts(payload: Sequence[dict[str, Any]]) -> list[Candle]:
    """Rebuild candles from :func:`candle_to_dict` output."""
    candles: list[Candle] = []
    for row in payload:
        try:
            candles.append(
                Candle(
                    open_time=_to_utc(int(row["open_time"])),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Malformed cached candle: {row!r}") from exc
    return candles
