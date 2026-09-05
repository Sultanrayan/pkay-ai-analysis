"""Data access layer: market data, news/sentiment and caching."""

from .cache import Cache, NullCache, RedisCache
from .manager import CandleBatch, MarketDataManager
from .news import NewsService
from .providers import (
    BinanceProvider,
    CandleProvider,
    DemoProvider,
    ProviderError,
    YahooProvider,
)

__all__ = [
    "BinanceProvider",
    "Cache",
    "CandleBatch",
    "CandleProvider",
    "DemoProvider",
    "MarketDataManager",
    "NewsService",
    "NullCache",
    "ProviderError",
    "RedisCache",
    "YahooProvider",
]
