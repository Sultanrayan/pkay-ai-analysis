"""JSON serialization for analysis reports."""

from __future__ import annotations

from typing import Any

from ..analysis.report import AnalysisReport


def report_to_dict(report: AnalysisReport) -> dict[str, Any]:
    """Serialize an :class:`AnalysisReport` into the public JSON shape."""
    return {
        "symbol": report.symbol.value,
        "timeframe": report.timeframe.value,
        "signal": report.final_signal,
        "score": round(report.decision.total_score, 2),
        "confidence": round(report.final_confidence, 2),
        "current_price": report.current_price,
        "agents": {
            "technical": round(report.technical.score, 2),
            "volume": round(report.volume.score, 2),
            "volatility": round(report.volatility.score, 2),
            "pattern": round(report.pattern.score, 2),
            "sentiment": round(report.sentiment.score, 2),
            "onchain": round(report.onchain.score, 2),
            "macro": round(report.macro.score, 2),
            "correlation": round(report.correlation.score, 2),
            "risk": round(report.risk.score, 2),
            "sniper": round(report.sniper.opportunity_score, 2),
        },
        "risk": {
            "stop_loss": report.risk.stop_loss,
            "take_profit": report.risk.take_profit,
            "position_size_pct": report.risk.position_size_pct,
            "atr": report.risk.atr,
            "volatility_label": report.risk.volatility_label,
        },
        "team_scores": report.decision.team_scores,
        "llm_enhanced": report.llm is not None,
        "summary": report.final_summary,
        "demo_data": report.any_demo_data,
        "response_time_ms": report.response_time_ms,
        "generated_at": report.created_at.isoformat(),
    }
