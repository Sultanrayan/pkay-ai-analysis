"""Analysis runner.

Orchestrates a single analysis request end to end:

    candles  -> technical agent
    sentiment -> sentiment agent
    candles  -> risk agent (bias from technical)
    both assets -> correlation agent
    all four -> decision engine

Kept deliberately thin: every step is delegated to a focused module so new
agents or data sources can be added without touching this flow.
"""

from __future__ import annotations

import logging
import time

from ..agents import correlation as correlation_agent
from ..agents import decision as decision_agent
from ..agents import risk as risk_agent
from ..agents import sentiment as sentiment_agent
from ..agents import technical as technical_agent
from ..agents.base import CorrelationResult
from ..data.manager import MarketDataManager
from ..domain import Candle, Symbol, Timeframe
from .report import AnalysisReport

logger = logging.getLogger(__name__)


class AnalysisRunner:
    """Composes the data manager and the four agents into reports."""

    def __init__(self, data_manager: MarketDataManager) -> None:
        self._data = data_manager

    async def analyze(self, symbol: Symbol, timeframe: Timeframe) -> AnalysisReport:
        started = time.perf_counter()

        batch = await self._data.get_candles(symbol, timeframe)
        candles: list[Candle] = batch.candles

        sentiment_snapshot = await self._data.get_sentiment(symbol)

        # Technical bias drives where the risk agent places SL/TP.
        technical = technical_agent.analyze(candles)
        direction = 1 if technical.score > 0 else -1 if technical.score < 0 else 0
        risk = risk_agent.analyze(candles, direction=direction)
        sentiment = sentiment_agent.analyze(sentiment_snapshot)
        correlation = await self._correlate(symbol, timeframe, candles)

        decision = decision_agent.decide(technical, sentiment, risk, correlation)

        response_time_ms = int((time.perf_counter() - started) * 1000)
        return AnalysisReport(
            symbol=symbol,
            timeframe=timeframe,
            current_price=candles[-1].close,
            technical=technical,
            sentiment=sentiment,
            risk=risk,
            correlation=correlation,
            decision=decision,
            candle_source=batch.source,
            is_demo_data=batch.is_demo,
            candles=candles,
            response_time_ms=response_time_ms,
        )

    async def _correlate(
        self, symbol: Symbol, timeframe: Timeframe, candles: list[Candle]
    ) -> CorrelationResult:
        """Correlate against the counterpart asset; neutral on any failure."""
        other_symbol = symbol.counterpart()
        try:
            other_batch = await self._data.get_candles(other_symbol, timeframe)
        except Exception as exc:
            logger.info("Correlation data unavailable for %s: %s", other_symbol.value, exc)
            return CorrelationResult(
                score=0.0,
                coefficient=None,
                other_symbol=other_symbol,
                divergence_note="counterpart data unavailable",
            )
        return correlation_agent.analyze(candles, other_batch.candles, other_symbol)
