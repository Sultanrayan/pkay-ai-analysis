"""AI Agent Team function catalogue (functions-only).

Backs ``POST /api/v3/agents``. The endpoint returns callable function
definitions (tools) for the AI Agent Team and *nothing else*: it never runs an
analysis and it never accepts or invokes a user supplied AI model.
"""

from __future__ import annotations

from typing import Any

#: Data Pair inputs every agent function accepts.
_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "symbol": {
            "type": "string",
            "enum": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XAUUSD"],
            "description": "Market symbol",
        },
        "timeframe": {
            "type": "string",
            "enum": ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
            "description": "Candle timeframe",
        },
    },
    "required": ["symbol", "timeframe"],
}


def _function(
    function_id: str,
    name: str,
    team: str,
    weight: float,
    description: str,
) -> dict[str, Any]:
    return {
        "id": function_id,
        "name": name,
        "team": team,
        "weight": weight,
        "description": description,
        "parameters": _PARAMETERS,
    }


#: The complete set of callable functions the AI Agent Team exposes.
FUNCTIONS: tuple[dict[str, Any], ...] = (
    _function("technical", "analyze_technical", "Technical", 0.35, "Trend, momentum and moving averages"),
    _function("volume", "analyze_volume", "Technical", 0.35, "OBV and volume flow analysis"),
    _function("volatility", "analyze_volatility", "Technical", 0.35, "Bollinger bands and band squeeze"),
    _function("pattern", "analyze_pattern", "Technical", 0.35, "Breakouts and chart patterns"),
    _function("sentiment", "analyze_sentiment", "Market Intel", 0.25, "News scoring and the Fear & Greed index"),
    _function("onchain", "analyze_onchain", "Market Intel", 0.25, "Whale activity and exchange flows"),
    _function("macro", "analyze_macro", "Market Intel", 0.25, "Rate policy, DXY and inflation"),
    _function("correlation", "analyze_correlation", "Market Intel", 0.25, "Cross-asset correlation"),
    _function("risk", "analyze_risk", "Risk", 0.2, "ATR stops and position sizing"),
    _function("sniper", "scan_sniper", "Sniper", 0.0, "Signal-only memecoin scan"),
)

_BY_ID = {f["id"]: f for f in FUNCTIONS}
_BY_NAME = {f["name"]: f for f in FUNCTIONS}


def functions_response(
    requested: list[str] | None = None,
    fmt: str = "tools",
) -> dict[str, Any]:
    """Build the functions-only response for ``POST /api/v3/agents``.

    ``requested`` selects functions by id or by callable name; ``None`` means
    every function. Raises :class:`ValueError` for unknown names so the HTTP
    handler can answer with ``400``.
    """
    if requested is None:
        selected = list(FUNCTIONS)
    else:
        if not isinstance(requested, list) or not all(
            isinstance(item, str) for item in requested
        ):
            raise ValueError("functions must be a list of strings")
        selected = []
        for raw in requested:
            found = _BY_ID.get(raw) or _BY_NAME.get(raw)
            if found is None:
                raise ValueError(f"Unknown function: {raw}")
            selected.append(found)

    tools = [
        {
            "name": f["name"],
            "description": f["description"],
            "parameters": f["parameters"],
        }
        for f in selected
    ]
    return {
        "endpoint": "/api/v3/agents",
        "format": fmt,
        "count": len(tools),
        "functions": tools,
    }
