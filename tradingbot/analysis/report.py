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
    MacroResult,
    OnChainResult,
    PatternResult,
    RiskResult,
    SentimentResult,
    SniperResult,
    TechnicalResult,
    VolatilityResult,
    VolumeResult,
)
from ..domain import Candle, Symbol, Timeframe, utcnow
from ..llm import LLMResult


@dataclass(slots=True)
class AnalysisReport:
    """Everything produced by one analysis run.

    ``candles`` is the input series (kept for chart rendering only; storage
    and history never persist it). ``llm`` holds DeepSeek's enrichment when
    it was available; ``final_*`` properties prefer it over the deterministic
    engine so the whole UI reads from one place.
    """

    symbol: Symbol
    timeframe: Timeframe
    current_price: float
    technical: TechnicalResult
    volume: VolumeResult
    volatility: VolatilityResult
    pattern: PatternResult
    sentiment: SentimentResult
    onchain: OnChainResult
    macro: MacroResult
    risk: RiskResult
    correlation: CorrelationResult
    sniper: SniperResult
    decision: DecisionResult
    candle_source: str = ""
    is_demo_data: bool = False
    candles: list[Candle] | None = None
    created_at: datetime = field(default_factory=utcnow)
    response_time_ms: int = 0
    row_id: int | None = None
    message_id: int | None = None
    llm: LLMResult | None = None

    # -- final signal (LLM when available, else the deterministic engine) ---

    @property
    def final_signal(self) -> str:
        return self.llm.signal if self.llm else self.decision.signal

    @property
    def final_confidence(self) -> float:
        return self.llm.confidence if self.llm else self.decision.confidence

    @property
    def final_summary(self) -> str:
        return self.llm.summary if self.llm else self.decision.summary

    @property
    def signal_source(self) -> str:
        return "ai" if self.llm else "engine"

    # -- provenance ---------------------------------------------------------

    @property
    def demo_sources(self) -> tuple[str, ...]:
        """Which inputs were simulated/heuristic in this run (for the notice)."""
        sources: list[str] = []
        if self.is_demo_data:
            sources.append("price")
        if self.sentiment.is_demo:
            sources.append("sentiment")
        if self.onchain.is_demo:
            sources.append("onchain")
        if self.macro.is_demo:
            sources.append("macro")
        if self.sniper.is_demo:
            sources.append("sniper")
        return tuple(sources)

    @property
    def any_demo_data(self) -> bool:
        """True when any input came from a simulated/demo source."""
        return bool(self.demo_sources)