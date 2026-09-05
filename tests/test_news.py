"""Tests for news sentiment scoring and RSS parsing."""

from __future__ import annotations

import pytest

from tradingbot.data.news import NewsService, aggregate_sentiment, score_headline
from tradingbot.data.providers import ProviderError
from tradingbot.domain import NewsItem

SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item><title>Bitcoin surges to record high</title><link>https://x/1</link></item>
    <item><title>Gold slumps on strong dollar</title><link>https://x/2</link></item>
  </channel>
</rss>
"""


def test_score_headline_direction():
    assert score_headline("Bitcoin surges to new record high") > 0
    assert score_headline("Gold craters amid sell-off") < 0
    assert score_headline("Markets trade flat") == 0


def test_aggregate_sentiment_bullish_environment():
    headlines = [NewsItem(title="Bitcoin surges on ETF approval and strong inflows")]
    snapshot = aggregate_sentiment(headlines, fear_greed_value=80.0, fear_greed_label="Extreme Greed")
    assert snapshot.overall_score > 0
    assert snapshot.news_score > 0
    assert snapshot.fear_greed_value == 80.0
    assert snapshot.news_count == 1


def test_aggregate_sentiment_bearish_environment():
    headlines = [NewsItem(title="Gold plunges as outflows accelerate")]
    snapshot = aggregate_sentiment(headlines, fear_greed_value=20.0, fear_greed_label="Extreme Fear")
    assert snapshot.overall_score < 0


def test_aggregate_neutral_when_no_inputs():
    snapshot = aggregate_sentiment([])
    assert snapshot.overall_score == 0.0
    assert snapshot.news_count == 0
    assert snapshot.social_volume > 0  # deterministic heuristic default


def test_rss_parsing_extracts_titles():
    items = NewsService._parse_rss(SAMPLE_RSS, "test-feed")
    assert [item.title for item in items] == [
        "Bitcoin surges to record high",
        "Gold slumps on strong dollar",
    ]


def test_rss_parsing_rejects_garbage():
    with pytest.raises(ProviderError):
        NewsService._parse_rss(b"<html>not an rss feed</html>", "bad-feed")


def test_rss_parsing_rejects_empty_items():
    empty = b'<?xml version="1.0"?><rss version="2.0"><channel><item></item></channel></rss>'
    with pytest.raises(ProviderError):
        NewsService._parse_rss(empty, "empty-feed")


def test_rss_parsing_handles_cdata():
    feed = b"""<?xml version="1.0"?><rss version="2.0"><channel>
      <item><title><![CDATA[Bitcoin rallies past key level]]></title><link>x</link></item>
    </channel></rss>"""
    items = NewsService._parse_rss(feed, "cdata-feed")
    assert items[0].title == "Bitcoin rallies past key level"


def test_rss_regex_fallback_handles_malformed_xml():
    # Unescaped ampersand makes this invalid XML, but headlines are salvageable.
    feed = b"""<?xml version="1.0"?><rss version="2.0"><channel>
      <item><title>Gold & silver surge to records</title><link>x</link></item>
      <item><title>Dollar &amp; yields move</title><link>y</link></item>
    </channel></rss>"""
    items = NewsService._parse_rss(feed, "messy-feed")
    titles = [item.title for item in items]
    assert "Gold & silver surge to records" in titles
    assert "Dollar & yields move" in titles
