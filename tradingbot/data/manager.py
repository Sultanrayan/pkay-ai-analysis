"""Data manager.

The single entry point the analysis layer uses for market data. It:

* routes each symbol to its preferred provider chain (live APIs first, then a
  deterministic demo provider when enabled or when everything else fails),
* transparently caches candle series in Redis (or a null cache),
* fetches and aggregates news sentiment with the same fallback behaviour.

Returning the resolved *source* alongside the data lets reports disclose when
data is demo/simulated instead of live.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ..config import Settings
from ..domain import Candle, NewsItem, SentimentSnapshot, Symbol, Timeframe
from .cache import Cache, NullCache
from .news import NewsService
from .providers import (
    BinanceProvider,
    CandleProvider,
    DemoProvider,
    ProviderError,
    YahooProvider,
    candle_to_dict,
    candles_from_dicts,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CandleBatch:
    """Candles plus provenance metadata for one fetch request."""

    candles: list[Candle]
    source: str
    from_cache: bool = False
    is_demo: bool = False


class MarketDataManager:
    """Coordinates providers, cache and news sentiment."""

    def __init__(
        self,
        client,
        settings: Settings,
        cache: Cache | None = None,
        news_service: NewsService | None = None,
    ) -> None:
        self._settings = settings
        self._cache: Cache = cache or NullCache()
        self._news = news_service or NewsService(client, settings)

        binance = BinanceProvider(client)
        yahoo = YahooProvider(client)
        demo = DemoProvider()
        if settings.use_demo_data:
            self._candle_chain: list[CandleProvider] = [demo]
        else:
            self._candle_chain = [binance, yahoo]
            if settings.demo_fallback:
                self._candle_chain.append(demo)
        self._sentiment_demo = DemoSentimentSource(settings)

    # -- candles -----------------------------------------------------------

    async def get_candles(
        self, symbol: Symbol, timeframe: Timeframe, limit: int = 500
    ) -> CandleBatch:
        """Return candles for ``symbol``/``timeframe``, from cache if fresh."""
        cache_key = f"candles:{symbol.value}:{timeframe.value}"
        cached = await self._cache.get(cache_key)
        if cached:
            try:
                return CandleBatch(
                    candles=candles_from_dicts(cached),
                    source="cache",
                    from_cache=True,
                )
            except ProviderError:
                logger.warning("Ignoring corrupt cache entry %r", cache_key)

        for provider in self._candle_chain:
            if not provider.supports(symbol):
                continue
            try:
                candles = await provider.fetch_candles(symbol, timeframe, limit=limit)
            except ProviderError as exc:
                logger.info("Provider %s failed for %s %s: %s",
                            provider.name, symbol.value, timeframe.value, exc)
                continue
            if len(candles) < 2:
                continue
            await self._cache.set(
                cache_key, [candle_to_dict(c) for c in candles], self._settings.candle_cache_ttl
            )
            logger.info(
                "Fetched %d %s candles for %s from %s",
                len(candles), timeframe.value, symbol.value, provider.name,
            )
            return CandleBatch(
                candles=candles,
                source=provider.name,
                is_demo=provider.is_demo,
            )
        raise ProviderError(
            f"No provider available for {symbol.value} {timeframe.value} "
            f"(live APIs failed and demo fallback is disabled)"
        )

    # -- sentiment ---------------------------------------------------------

    async def get_sentiment(self, symbol: Symbol) -> SentimentSnapshot:
        """Return an aggregated sentiment snapshot for ``symbol``."""
        if self._settings.use_demo_data:
            return self._sentiment_demo.build(symbol)
        try:
            return await self._news.fetch(symbol)
        except ProviderError as exc:
            if self._settings.demo_fallback:
                logger.info("Live sentiment unavailable (%s); using demo source", exc)
                return self._sentiment_demo.build(symbol)
            raise


class DemoSentimentSource:
    """Deterministic offline sentiment generator (clearly flagged as demo)."""

    #: Stable per-symbol demo profiles so reports look sane offline.
    _PROFILES: dict[Symbol, tuple[float, float, str]] = {
        # symbol -> (fear&greed value, f&g label, headline seed text)
        Symbol.BTCUSD: (64.0, "Greed", "Bitcoin ETF demand strengthens as institutions accumulate"),
        Symbol.XAUUSD: (56.0, "Greed", "Gold demand rises on safe-haven inflows amid uncertainty"),
    }

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build(self, symbol: Symbol) -> SentimentSnapshot:
        from .news import aggregate_sentiment

        fng_value, fng_label, seed_title = self._PROFILES.get(
            symbol, (50.0, "Neutral", "Markets move sideways")
        )
        headlines = [NewsItem(title=seed_title, url="", source="demo")]
        return aggregate_sentiment(
            headlines=headlines,
            fear_greed_value=fng_value,
            fear_greed_label=fng_label,
            sources=("demo",),
            is_demo=True,
        )
