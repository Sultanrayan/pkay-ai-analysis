"""Report export helpers.

Turns a stored analysis history row into a portable CSV document that the bot
sends to the user. CSV keeps the standard library only; adding PDF later
means adding one function here.
"""

from __future__ import annotations

import csv
import io

from .storage.models import HistoryRow

COLUMNS = [
    "timestamp", "symbol", "timeframe", "current_price", "technical_score",
    "sentiment_score", "risk_score", "correlation_score", "total_score",
    "signal", "rsi", "macd", "ma_50", "ma_200", "support", "resistance",
    "stop_loss", "take_profit", "position_size_pct", "atr", "summary",
]


def history_row_to_csv(row: HistoryRow) -> str:
    """Serialize one history row into CSV text (header included)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    writer.writerow([
        row.timestamp.isoformat() if row.timestamp else "",
        row.symbol,
        row.timeframe,
        row.current_price,
        row.technical_score,
        row.sentiment_score,
        row.risk_score,
        row.correlation_score,
        row.total_score,
        row.signal,
        row.rsi,
        row.macd,
        row.ma_50,
        row.ma_200,
        row.support,
        row.resistance,
        row.stop_loss,
        row.take_profit,
        row.position_size_pct,
        row.atr,
        row.summary,
    ])
    return buffer.getvalue()
