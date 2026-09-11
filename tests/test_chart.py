"""Tests for Pillow chart rendering."""

from __future__ import annotations

import pytest
from conftest import make_candles

from tradingbot.charts import render_chart


def test_render_chart_writes_png(tmp_path):
    candles = make_candles(count=120)
    output = tmp_path / "chart.png"
    render_chart(candles, output, title="BTCUSDT 1H")
    assert output.exists()
    assert output.stat().st_size > 0
    # PNG magic bytes.
    assert output.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_chart_requires_two_candles(tmp_path):
    with pytest.raises(ValueError):
        render_chart(make_candles(count=1), tmp_path / "x.png", title="t")


def test_render_chart_accepts_ma_overlays(tmp_path):
    candles = make_candles(count=90)
    output = tmp_path / "with_ma.png"
    closes = [c.close for c in candles]
    render_chart(candles, output, title="XAUUSD 1H", ma_series=[closes, closes])
    assert output.exists()
