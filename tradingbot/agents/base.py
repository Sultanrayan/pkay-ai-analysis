"""Agent result models.

Each agent is a *pure function* from data to one of these frozen result
objects. Keeping them plain dataclasses (no behaviour, no I/O) means they are
trivially testable and can be serialized into the analysis history row.
Every result carries a directional ``score`` in the range -100..+100 so the
decision engine can combine them with fixed weights (the sniper uses a
0..100 opportunity scale instead because it is informational, not
part of the directional call).
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
class VolumeResult:
    score: float  # -100..+100
    obv_slope: float | None  # -1..+1, normalized OBV trend over the window
    volume_ratio: float  # latest volume / SMA(20) volume (1.0 = average)
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class VolatilityResult:
    score: float  # -100..+100
    atr_pct: float  # ATR as % of price
    band_width_pct: float  # Bollinger width as % of the middle band
    band_position: float  # -1 (below lower band) .. +1 (above upper band)
    squeeze: bool  # bands unusually tight -> expansion imminent
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class PatternResult:
    score: float  # -100..+100
    breakout: str  # bullish | bearish | none
    support: float | None
    resistance: float | None
    proximity: float  # -1 (at support) .. +1 (at resistance)
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class OnChainResult:
    score: float  # -100..+100
    whale_activity: float
    exchange_netflow: float
    active_addresses: float
    mvrv: float | None
    sopr: float | None
    is_demo: bool
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MacroResult:
    score: float  # -100..+100
    rate_trend: float  # -1..+1
    dxy_trend: float  # -1..+1
    inflation_trend: float  # -1..+1
    is_demo: bool
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SniperOpportunity:
    """One ranked candidate shown in the (signal-only) sniper report."""

    symbol: str
    chain: str
    liquidity_usd: float
    hype_score: float
    safety_score: float
    price_change_pct: float
    risk_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SniperResult:
    """Signal-only sniper outcome: an opportunity score + ranked candidates.

    ``opportunity_score`` is 0..100 for the top candidate. Reports must make
    clear the scan never places orders.
    """

    opportunity_score: float
    safety_score: float
    opportunities: tuple[SniperOpportunity, ...] = ()
    is_demo: bool = True
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
    total_score: float  # -100..+100 (directional, sniper excluded)
    signal: str  # Signal enum value (BUY / SELL / HOLD)
    confidence: float  # 0..100, from agent agreement
    team_scores: dict[str, float]  # technical / market_intel / risk / sniper
    contributions: dict[str, float]  # team -> weighted directional contribution
    summary: str  # human readable English summary (also persisted)
