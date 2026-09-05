"""Correlation Analysis Agent.

Measures the Pearson correlation between two assets' log returns over their
shared candle window. Interpretation used here:

* Strong positive correlation -> the two assets move together (low
  diversification); the agent contributes a small positive score as
  cross-confirmation.
* Near-zero / negative correlation -> divergence; useful context but
  contributes ~0 to the directional call.

The correlation weight in the decision engine is deliberately the smallest
(0.1) because correlation describes the *pair*, not either asset's outlook.
"""

from __future__ import annotations

from ..domain import Candle, Symbol
from ..indicators import clamp, correlation, log_returns
from .base import CorrelationResult

#: Number of trailing closes (per asset) used for the return series.
SAMPLE_WINDOW = 120

#: |r| above this counts as "correlated".
CORRELATED_THRESHOLD = 0.5


def analyze(
    candles_a: list[Candle],
    candles_b: list[Candle],
    other_symbol: Symbol | None = None,
) -> CorrelationResult:
    """Correlate the returns of two candle series.

    ``candles_a`` belongs to the analyzed symbol, ``candles_b`` to the other
    asset; ``other_symbol`` is only used for the informational result field.
    """
    closes_a = [c.close for c in candles_a[-SAMPLE_WINDOW:]]
    closes_b = [c.close for c in candles_b[-SAMPLE_WINDOW:]]

    if len(closes_a) < 15 or len(closes_b) < 15:
        return CorrelationResult(
            score=0.0,
            coefficient=None,
            other_symbol=other_symbol,
            divergence_note="not enough data to correlate",
        )

    n = min(len(closes_a), len(closes_b))
    returns_a = log_returns(closes_a[-n:])
    returns_b = log_returns(closes_b[-n:])
    coefficient = correlation(returns_a, returns_b)

    notes: list[str] = []
    divergence_note: str | None = None
    if coefficient is None:
        score = 0.0
        divergence_note = "return series have no measurable correlation"
    else:
        abs_r = abs(coefficient)
        if abs_r >= CORRELATED_THRESHOLD:
            relation = "positively" if coefficient > 0 else "negatively"
            notes.append(f"assets strongly {relation} correlated (r={coefficient:.2f})")
        else:
            divergence_note = (
                f"low correlation (r={coefficient:.2f}) — assets behave independently"
            )
            notes.append("low correlation detected — divergence opportunity context")
        # Temper the raw coefficient so correlation alone never dominates.
        score = clamp(coefficient * 50.0)

    return CorrelationResult(
        score=round(score, 1),
        coefficient=round(coefficient, 3) if coefficient is not None else None,
        other_symbol=other_symbol,
        divergence_note=divergence_note,
        notes=tuple(notes),
    )
