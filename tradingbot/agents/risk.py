"""Risk Management Agent.

Derives stop-loss / take-profit levels from the ATR(14), sizes a suggested
position from a fixed per-trade account risk, and scores how "tradeable" the
current volatility regime is.

Defaults are module constants so the risk profile is tuned in one place:

* ``SL_MULT`` / ``TP_MULT``  ATR multiples for stop-loss / take-profit.
* ``RISK_PER_TRADE_PCT``    % of account risked per trade (fixed-fractional).
* Position size (% of account) = RISK_PER_TRADE_PCT / stop distance (%).
"""

from __future__ import annotations

from ..domain import Candle
from ..indicators import atr_series, clamp
from .base import RiskResult

SL_MULT = 1.5
TP_MULT = 2.5
RISK_PER_TRADE_PCT = 1.0
MAX_POSITION_PCT = 100.0


def analyze(candles: list[Candle], direction: int) -> RiskResult:
    """Score risk for the latest candle.

    ``direction`` (+1 / -1 / 0) comes from the technical agent's bias and
    decides whether the stop/target levels sit below or above the market.
    """
    if len(candles) < 15:
        raise ValueError("Risk analysis needs at least 15 candles")
    direction = int(max(-1, min(1, direction)))

    last = candles[-1]
    entry = last.close
    atr_value = atr_series(candles, period=14)[-1]
    if atr_value is None or atr_value <= 0:
        raise ValueError("ATR unavailable — cannot size risk")
    atr_pct = atr_value / entry * 100.0

    if direction > 0:  # long bias: stop below, target above
        stop_loss = entry - SL_MULT * atr_value
        take_profit = entry + TP_MULT * atr_value
    elif direction < 0:  # short bias: stop above, target below
        stop_loss = entry + SL_MULT * atr_value
        take_profit = entry - TP_MULT * atr_value
    else:  # neutral: present the long-side framing as a reference
        stop_loss = entry - SL_MULT * atr_value
        take_profit = entry + TP_MULT * atr_value

    stop_pct = abs(stop_loss - entry) / entry * 100.0
    take_profit_pct = abs(take_profit - entry) / entry * 100.0

    # Fixed-fractional sizing: risk a set % of the account, expressed as a
    # position fraction of the account sized so the stop only costs that much.
    position_size_pct = (
        RISK_PER_TRADE_PCT / stop_pct * 100.0 if stop_pct > 0 else MAX_POSITION_PCT
    )
    position_size_pct = clamp(position_size_pct, 0.0, MAX_POSITION_PCT)

    if atr_pct < 0.8:
        volatility_label = "Low"
    elif atr_pct < 2.0:
        volatility_label = "Medium"
    elif atr_pct < 4.0:
        volatility_label = "High"
    else:
        volatility_label = "Extreme"

    # Score: volatility regime + directionality + stop sanity.
    score = 0.0
    if atr_pct < 0.8:
        score += 40.0
    elif atr_pct < 1.5:
        score += 25.0
    elif atr_pct < 2.5:
        score += 0.0
    elif atr_pct < 4.0:
        score -= 40.0
    else:
        score -= 70.0
    if direction != 0:
        score += 25.0  # directional setup has defined SL/TP structure
    if 0.2 <= stop_pct <= 8.0:
        score += 15.0
    else:
        score -= 15.0
    risk_score = round(clamp(score), 1)

    notes = [
        f"ATR {atr_value:.2f} ({atr_pct:.2f}%/candle, {volatility_label} volatility)",
        f"SL {SL_MULT:g}xATR, TP {TP_MULT:g}xATR with {RISK_PER_TRADE_PCT:g}% account risk",
    ]

    return RiskResult(
        score=risk_score,
        atr=round(atr_value, 6),
        atr_pct=round(atr_pct, 2),
        stop_loss=round(stop_loss, 2),
        take_profit=round(take_profit, 2),
        stop_pct=round(stop_pct, 2),
        take_profit_pct=round(take_profit_pct, 2),
        position_size_pct=round(position_size_pct, 2),
        volatility_label=volatility_label,
        direction=direction,
        notes=tuple(notes),
    )
