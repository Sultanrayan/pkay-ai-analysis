"""Storage models.

Plain dataclasses that mirror the SQL schema in :file:`schema.sql` plus the
mapping from an :class:`~tradingbot.analysis.report.AnalysisReport` into a
persistable history row.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from ..analysis.report import AnalysisReport
from ..domain import Symbol, Timeframe


@dataclass(slots=True)
class TelegramUser:
    user_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str = "en"
    daily_requests: int = 0
    last_request_date: date | None = None
    max_daily_requests: int = 10
    is_premium: bool = False
    created_at: datetime | None = None
    last_active: datetime | None = None

    @property
    def language(self) -> str:
        """Bot language: khmer when the user prefers it, else english."""
        return "kh" if (self.language_code or "").lower().startswith("kh") else "en"


@dataclass(slots=True)
class UserPreferences:
    user_id: int
    default_symbol: Symbol = Symbol.BTCUSD
    default_timeframe: Timeframe = Timeframe.H1
    show_chart: bool = True
    show_indicators: bool = True
    show_risk: bool = True
    show_sentiment: bool = True
    notification_enabled: str = "daily"
    updated_at: datetime | None = None


@dataclass(slots=True)
class HistoryRow:
    """One row of ``analysis_history`` (all fields optional except ``user_id``)."""

    user_id: int
    id: int | None = None
    symbol: str = ""
    timeframe: str = ""
    timestamp: datetime | None = None
    current_price: float | None = None
    technical_score: int | None = None
    sentiment_score: int | None = None
    risk_score: int | None = None
    correlation_score: int | None = None
    total_score: int | None = None
    signal: str | None = None
    rsi: float | None = None
    macd: float | None = None
    ma_50: float | None = None
    ma_200: float | None = None
    support: float | None = None
    resistance: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float | None = None
    atr: float | None = None
    summary: str | None = None
    chart_url: str | None = None
    response_time_ms: int | None = None
    message_id: int | None = None


def history_row_from_report(report: AnalysisReport, user_id: int) -> HistoryRow:
    """Map a fresh report into a history row (id/message_id still unset)."""
    return HistoryRow(
        id=None,
        user_id=user_id,
        symbol=report.symbol.value,
        timeframe=report.timeframe.value,
        timestamp=report.created_at,
        current_price=report.current_price,
        technical_score=round(report.technical.score),
        sentiment_score=round(report.sentiment.score),
        risk_score=round(report.risk.score),
        correlation_score=round(report.correlation.score),
        total_score=round(report.decision.total_score),
        signal=report.decision.signal,
        rsi=report.technical.rsi,
        macd=report.technical.macd,
        ma_50=report.technical.ma_50,
        ma_200=report.technical.ma_200,
        support=report.technical.support,
        resistance=report.technical.resistance,
        stop_loss=report.risk.stop_loss,
        take_profit=report.risk.take_profit,
        position_size_pct=report.risk.position_size_pct,
        atr=report.risk.atr,
        summary=report.decision.summary,
        response_time_ms=report.response_time_ms,
    )
