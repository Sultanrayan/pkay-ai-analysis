"""Analysis report model — the complete result of one analysis run.

Holds the raw agent results plus provenance metadata. Formatting for display
and persistence mapping live elsewhere (formatter / storage) so this stays a
plain data carrier.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..agents.base import (
    CorrelationResult,
    DecisionResult,
    RiskResult,
    SentimentResult,
    TechnicalResult,
)
from ..domain import Candle, Symbol, Timeframe, utcnow


@dataclass(slots=True)
class AnalysisReport:
    """Everything produced by one analysis run.

    ``candles`` is the input series (kept for chart rendering only; storage
    and history never persist it).
    """

    symbol: Symbol
    timeframe: Timeframe
    current_price: float
    technical: TechnicalResult
    sentiment: SentimentResult
    risk: RiskResult
    correlation: CorrelationResult
    decision: DecisionResult
    candle_source: str = ""
    is_demo_data: bool = False
    candles: list[Candle] | None = None
    created_at: datetime = field(default_factory=utcnow)
    response_time_ms: int = 0
    row_id: int | None = None
    message_id: int | None = None

    @property
    def any_demo_data(self) -> bool:
        """True when price or sentiment came from simulated demo sources."""
        return self.is_demo_data or self.sentiment.is_demo
