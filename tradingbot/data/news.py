"""News & sentiment service.

Fetches symbol-scoped news headlines over RSS and the Crypto Fear & Greed
index (alternative.me), then scores them into a
:class:`~tradingbot.domain.SentimentSnapshot`. All scoring logic is pure
(``score_headline`` / ``aggregate_sentiment``) so it can be unit tested
offline; only the fetching is I/O bound.

The Fear & Greed index is crypto-centric; for XAUUSD it is used as a generic
"risk appetite" proxy. ``social_volume`` is a documented heuristic estimate
(no free keyless social-volume API exists) and is reported as informational.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from html import unescape as html_unescape
from typing import Any

import httpx

from ..config import Settings
from ..domain import NewsItem, SentimentSnapshot, Symbol
from .providers import DEFAULT_HEADERS, ProviderError

logger = logging.getLogger(__name__)

#: (token, weight) lexicon used to score a single headline. Weights let a few
#: strong words (approval/ban) outweigh weaker chatter.
BULLISH_TERMS: dict[str, float] = {
    "surge": 1.0, "surges": 1.0, "rally": 1.0, "rallies": 1.0, "gains": 0.8,
    "gain": 0.6, "rise": 0.7, "rises": 0.7, "rising": 0.7, "jumps": 0.8,
    "soars": 1.0, "bullish": 1.0, "breakout": 1.0, "record": 0.8, "high": 0.5,
    "boost": 0.8, "boosts": 0.8, "strengthens": 0.8, "inflows": 0.9,
    "approval": 1.0, "approved": 1.0, "approve": 0.9, "etf": 0.7, "adoption": 0.8,
    "buy": 0.6, "buys": 0.6, "buying": 0.7, "positive": 0.7, "growth": 0.8,
    "all-time": 1.0, "reclaims": 0.9, "tops": 0.8, "beat": 0.7, "strong": 0.6,
    "support": 0.4, "accumulate": 0.6, "accumulation": 0.7, "demand": 0.6,
    "rebound": 0.8, "outperform": 0.8, "outlook": 0.4, "upgrade": 0.7,
}
BEARISH_TERMS: dict[str, float] = {
    "plunge": 1.0, "plunges": 1.0, "drop": 0.9, "drops": 0.9, "dropping": 0.8,
    "fall": 0.8, "falls": 0.8, "falling": 0.8, "slump": 1.0, "slumps": 1.0,
    "tumble": 1.0, "tumbles": 1.0, "crash": 1.0, "crashes": 1.0, "bearish": 1.0,
    "breakdown": 1.0, "low": 0.5, "selloff": 1.0, "sell-off": 1.0, "outflows": 0.9,
    "ban": 1.0, "banned": 1.0, "loss": 0.7, "losses": 0.7, "negative": 0.7,
    "rejection": 0.8, "reject": 0.7, "below": 0.5, "weak": 0.6, "weakness": 0.7,
    "sell": 0.6, "sells": 0.6, "selling": 0.7, "warning": 0.7, "warns": 0.7,
    "decline": 0.8, "declines": 0.8, "hack": 1.0, "hacked": 1.0, "fraud": 1.0,
    "lawsuit": 0.8, "crackdown": 0.9, "volatile": 0.5, "uncertainty": 0.6,
    "correction": 0.8, "pressure": 0.6, "slips": 0.8, "slides": 0.8,
    "cut": 0.6, "cuts": 0.6, "reduction": 0.5, "capitulation": 1.0,
}

_WORD_RE = re.compile(r"[a-z0-9'+-]+")


def score_headline(title: str) -> float:
    """Score one headline in the range -1 (bearish) to +1 (bullish)."""
    tokens = set(_WORD_RE.findall(title.lower()))
    bull = sum(weight for term, weight in BULLISH_TERMS.items() if term in tokens)
    bear = sum(weight for term, weight in BEARISH_TERMS.items() if term in tokens)
    if bull == 0.0 and bear == 0.0:
        return 0.0
    return max(-1.0, min(1.0, (bull - bear) / (bull + bear)))


def _fear_greed_component(value: float) -> float:
    """Map the 0-100 Fear & Greed index onto -100 (extreme fear)..+100."""
    return max(-100.0, min(100.0, (value - 50.0) * 2.0))


def _estimate_social_volume(fear_greed_value: float | None, news_count: int) -> int:
    """Deterministic heuristic for social volume when no API is available."""
    fng = fear_greed_value if fear_greed_value is not None else 50.0
    return max(0, int(fng * 4.0 + news_count * 18.0 + 120.0))


def aggregate_sentiment(
    headlines: list[NewsItem],
    fear_greed_value: float | None = None,
    fear_greed_label: str | None = None,
    social_volume: int | None = None,
    sources: tuple[str, ...] = (),
    is_demo: bool = False,
) -> SentimentSnapshot:
    """Combine headlines + Fear & Greed into one sentiment snapshot.

    ``overall_score = 0.6 * news_score + 0.4 * fear_greed_component`` — news
    carries more weight because it is symbol-specific while the index is a
    market-wide proxy. Missing inputs contribute neutrally.
    """
    news_score = (
        (sum(score_headline(h.title) for h in headlines) / len(headlines) * 100.0)
        if headlines
        else 0.0
    )
    fng_component = (
        _fear_greed_component(fear_greed_value) if fear_greed_value is not None else 0.0
    )
    overall = max(-100.0, min(100.0, 0.6 * news_score + 0.4 * fng_component))
    social = social_volume if social_volume is not None else _estimate_social_volume(
        fear_greed_value, len(headlines)
    )
    return SentimentSnapshot(
        news_score=round(news_score, 2),
        news_count=len(headlines),
        headlines=tuple(headlines[:5]),
        fear_greed_value=fear_greed_value if fear_greed_value is not None else 50.0,
        fear_greed_label=fear_greed_label or "Neutral",
        social_volume=social,
        overall_score=round(overall, 2),
        sources=sources or ("aggregated",),
        is_demo=is_demo,
    )


class NewsService:
    """Fetches live headlines + Fear & Greed and produces sentiment snapshots.

    Raises :class:`ProviderError` when the live sources are unreachable so the
    caller (data manager) can fall back to the deterministic demo provider.
    """

    MAX_HEADLINES = 25

    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def fetch(self, symbol: Symbol) -> SentimentSnapshot:
        feed_url = self._settings.news_feed_for(symbol)
        headlines = await self._fetch_headlines(feed_url, symbol)
        fear_greed = await self._fetch_fear_greed()
        return aggregate_sentiment(
            headlines=headlines,
            fear_greed_value=fear_greed[0] if fear_greed else None,
            fear_greed_label=fear_greed[1] if fear_greed else None,
            sources=(feed_url,),
        )

    async def _fetch_headlines(self, feed_url: str, symbol: Symbol) -> list[NewsItem]:
        try:
            response = await self._client.get(
                feed_url, headers=DEFAULT_HEADERS, timeout=12.0, follow_redirects=True
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"News feed request failed for {symbol.value}: {exc}") from exc
        return self._parse_rss(response.content, feed_url)

    @staticmethod
    def _parse_rss(content: bytes, source: str) -> list[NewsItem]:
        """Extract ``<item><title>`` entries from an RSS/Atom feed.

        Some public feeds ship slightly malformed XML (unescaped ampersands,
        stray control characters). ``ElementTree`` handles well-formed feeds;
        a conservative regex fallback keeps those feeds usable.
        """
        try:
            items = NewsService._parse_rss_element_tree(content, source)
        except ET.ParseError:
            items = NewsService._parse_rss_regex(content, source)
        if not items:
            raise ProviderError(f"No headlines parsed from {source}")
        return items[: NewsService.MAX_HEADLINES]

    @staticmethod
    def _parse_rss_element_tree(content: bytes, source: str) -> list[NewsItem]:
        """Strict XML parse; raises ``ET.ParseError`` on malformed input."""
        items: list[NewsItem] = []
        root = ET.fromstring(content)
        for node in root.iter():
            tag = node.tag.lower()
            if not (tag.endswith("item") or tag.endswith("entry")):
                continue
            title = link = ""
            for child in node:
                child_tag = child.tag.lower()
                if child_tag.endswith("title"):
                    # itertext() also captures CDATA sections.
                    title = "".join(child.itertext()).strip()
                elif child_tag.endswith("link"):
                    link = child.text.strip() if child.text else (child.get("href") or "")
            if title:
                items.append(NewsItem(title=title, url=link, source=source))
        return items

    @staticmethod
    def _parse_rss_regex(content: bytes, source: str) -> list[NewsItem]:
        """Lenient fallback for feeds that are not well-formed XML."""
        text = content.decode("utf-8", errors="replace")
        items: list[NewsItem] = []
        block_pattern = re.compile(r"<(?:item|entry)\b[^>]*>(.*?)</(?:item|entry)>", re.DOTALL | re.IGNORECASE)
        title_pattern = re.compile(r"<title\b[^>]*>(.*?)</title>", re.DOTALL | re.IGNORECASE)
        for block in block_pattern.finditer(text):
            match = title_pattern.search(block.group(1))
            if not match:
                continue
            raw = match.group(1).replace("<![CDATA[", "").replace("]]>", "")
            raw = re.sub(r"<[^>]+>", "", raw)  # strip any inner tags
            title = html_unescape(raw).strip()
            if title:
                items.append(NewsItem(title=title, source=source))
        return items

    async def _fetch_fear_greed(self) -> tuple[float, str] | None:
        try:
            response = await self._client.get(
                self._settings.fear_greed_api_url, timeout=8.0, follow_redirects=True
            )
            response.raise_for_status()
            data: Any = response.json()
            entry = data["data"][0]
            return float(entry["value"]), str(entry["value_classification"])
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.info("Fear & Greed index unavailable (%s); using neutral input", exc)
            return None
