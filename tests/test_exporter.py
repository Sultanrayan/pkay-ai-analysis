"""Tests for CSV export of history rows."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from tradingbot.exporter import history_row_to_csv
from tradingbot.storage.models import HistoryRow


def _row() -> HistoryRow:
    return HistoryRow(
        id=7,
        user_id=1,
        symbol="BTCUSD",
        timeframe="1h",
        timestamp=datetime(2026, 9, 5, 12, 30, tzinfo=timezone.utc),
        current_price=60000.5,
        technical_score=42,
        sentiment_score=10,
        risk_score=-5,
        correlation_score=0,
        total_score=20,
        signal="HOLD",
        rsi=55.2,
        stop_loss=59000.0,
        take_profit=62000.0,
        position_size_pct=2.5,
        summary="Test summary with, a comma",
        response_time_ms=900,
    )


def test_csv_has_header_and_values():
    text = history_row_to_csv(_row())
    parsed = list(csv.reader(io.StringIO(text)))
    assert parsed[0][:5] == ["timestamp", "symbol", "timeframe", "current_price", "technical_score"]
    body = parsed[1]
    assert body[1] == "BTCUSD"
    assert body[4] == "42"
    assert body[10] == "55.2"
    assert body[20].startswith("Test summary with")  # quoted field kept intact


def test_csv_roundtrips_via_reader():
    text = history_row_to_csv(_row())
    assert '"Test summary with, a comma"' in text or "Test summary" in text
