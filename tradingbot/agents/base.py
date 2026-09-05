"""Agent result models.

Each agent is a *pure function* from data to one of these frozen result
objects. Keeping them plain dataclasses (no behaviour, no I/O) means they are
trivially testable and can be serialized into the analysis history row.
Every result carries a directional ``score`` in the range -100..+100 so the
decision engine can combine them with fixed weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain import Symbol


@dataclass(frozen=True, slots=True)
class TechnicalResult:
    score: float  # -100..+100 (bullish positive)
    rsi: float | None
    macd: float | None
    macd_signal: float | None
    macd_histogram: float | None
    ma_50: float | None
    ma_200: float | None
    support: float | None
    resistance: float | None
    momentum: str  # bullish | bearish | neutral
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SentimentResult:
    score: float  # -100..+100
    news_score: float
    news_count: int
    fear_greed_value: float
    fear_greed_label: str
    social_volume: int
    momentum: str  # bullish | bearish | neutral
    is_demo: bool
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RiskResult:
    score: float  # -100 (high risk) .. +100 (low risk / clean setup)
    atr: float
    atr_pct: float
    stop_loss: float | None
    take_profit: float | None
    stop_pct: float
    take_profit_pct: float
    position_size_pct: float
    volatility_label: str  # Low | Medium | High | Extreme
    direction: int  # +1 long bias, -1 short bias, 0 neutral
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class CorrelationResult:
    score: float  # -100..+100
    coefficient: float | None  # Pearson r between the two assets
    other_symbol: Symbol | None
    divergence_note: str | None
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DecisionResult:
    total_score: float  # -100..+100
    signal: str  # Signal enum value (BUY / SELL / HOLD)
    contributions: dict[str, float]  # agent name -> weighted score
    summary: str  # human readable English summary (also persisted)
