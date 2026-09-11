"""Analysis runner.

Orchestrates a single analysis request end to end (V3 multi-agent flow):

    candles            -> technical, volume, volatility, pattern agents
    sentiment snapshot -> sentiment agent
    on-chain snapshot  -> on-chain agent
    macro snapshot     -> macro agent
    both assets        -> correlation agent
    sniper scan        -> sniper agent (signal-only)
    all results        -> decision engine (+ optional DeepSeek enrichment)

Kept deliberately thin: every step is delegated to a focused module so new
agents or data sources can be added without touching this flow.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from ..agents import correlation as correlation_agent
from ..agents import decision as decision_agent
from ..agents import macro as macro_agent
from ..agents import onchain as onchain_agent
from ..agents import pattern as pattern_agent
from ..agents import risk as risk_agent
from ..agents import sentiment as sentiment_agent
from ..agents import sniper as sniper_agent
from ..agents import technical as technical_agent
from ..agents import volatility as volatility_agent
from ..agents import volume as volume_agent
from ..agents.base import CorrelationResult, DecisionResult
from ..config import Settings
from ..data.manager import MarketDataManager
from ..domain import Candle, Symbol, Timeframe
from ..llm import LLMResult
from .report import AnalysisReport

if TYPE_CHECKING:
    from ..llm import DeepSeekClient

logger = logging.getLogger(__name__)


class AnalysisRunner:
    """Composes the data manager, the ten agents and the optional LLM."""

    def __init__(
        self,
        data_manager: MarketDataManager,
        settings: Settings,
        llm: DeepSeekClient | None = None,
    ) -> None:
        self._data = data_manager
        self._settings = settings
        self._llm = llm

    async def analyze(self, symbol: Symbol, timeframe: Timeframe) -> AnalysisReport:
        started = time.perf_counter()

        batch = await self._data.get_candles(symbol, timeframe)
        candles: list[Candle] = batch.candles

        sentiment_snapshot = await self._data.get_sentiment(symbol)
        onchain_snapshot = await self._data.get_onchain(symbol)
        macro_snapshot = await self._data.get_macro()

        # Technical family: trend/momentum, volume, volatility regime, pattern.
        technical = technical_agent.analyze(candles)
        volume = volume_agent.analyze(candles)
        volatility = volatility_agent.analyze(candles)
        pattern = pattern_agent.analyze(candles)

        # Technical bias drives where the risk agent places SL/TP.
        direction = 1 if technical.score > 0 else -1 if technical.score < 0 else 0
        risk = risk_agent.analyze(candles, direction=direction)

        sentiment = sentiment_agent.analyze(sentiment_snapshot)
        onchain = onchain_agent.analyze(onchain_snapshot)
        macro = macro_agent.analyze(macro_snapshot)
        correlation = await self._correlate(symbol, timeframe, candles)

        sniper_scan = await self._data.get_sniper_scan()
        sniper = sniper_agent.analyze(
            sniper_scan,
            min_liquidity=self._settings.sniper_min_liquidity,
            max_opportunities=self._settings.sniper_max_opportunities,
        )

        decision = decision_agent.decide(
            technical, volume, volatility, pattern, sentiment, onchain, macro,
            correlation, risk, sniper,
        )

        llm = await self._enrich(symbol, timeframe, candles, decision) if self._llm else None

        response_time_ms = int((time.perf_counter() - started) * 1000)
        return AnalysisReport(
            symbol=symbol,
            timeframe=timeframe,
            current_price=candles[-1].close,
            technical=technical,
            volume=volume,
            volatility=volatility,
            pattern=pattern,
            sentiment=sentiment,
            onchain=onchain,
            macro=macro,
            risk=risk,
            correlation=correlation,
            sniper=sniper,
            decision=decision,
            candle_source=batch.source,
            is_demo_data=batch.is_demo,
            candles=candles,
            response_time_ms=response_time_ms,
            llm=llm,
        )

    async def _enrich(
        self,
        symbol: Symbol,
        timeframe: Timeframe,
        candles: list[Candle],
        decision: DecisionResult,
    ) -> LLMResult | None:
        """Ask DeepSeek to review the agent consensus (best-effort)."""
        assert self._llm is not None
        context = {
            "asset": symbol.value,
            "timeframe": timeframe.value,
            "current_price": candles[-1].close,
            "deterministic_signal": decision.signal,
            "deterministic_score": decision.total_score,
            "deterministic_summary": decision.summary,
            "team_scores": decision.team_scores,
        }
        return await self._llm.enhance(context)

    async def _correlate(
        self, symbol: Symbol, timeframe: Timeframe, candles: list[Candle]
    ) -> CorrelationResult:
        """Correlate against the peer asset; neutral on any failure."""
        other_symbol = symbol.correlation_peer()
        try:
            other_batch = await self._data.get_candles(other_symbol, timeframe)
        except Exception as exc:
            logger.info("Correlation data unavailable for %s: %s", other_symbol.value, exc)
            return CorrelationResult(
                score=0.0,
                coefficient=None,
                other_symbol=other_symbol,
                divergence_note="peer asset data unavailable",
            )
        return correlation_agent.analyze(candles, other_batch.candles, other_symbol)