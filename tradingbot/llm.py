"""DeepSeek-V4-Flash signal enrichment.

The deterministic decision engine always produces the baseline signal; when
``DEEPSEEK_API_KEY`` is configured this client asks DeepSeek-V4-Flash to
*review* the agent outputs and return a final signal, confidence and a short
summary. Any failure (missing key, network error, malformed JSON, invalid
signal) degrades gracefully to ``None`` and the caller keeps the
deterministic result — an LLM outage never breaks a report.

The API is OpenAI-compatible (``POST {base}/chat/completions``) and is
called directly with httpx so no extra dependency is needed.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from .config import Settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior trading analyst reviewing multi-agent analysis output. "
    "Return ONLY a JSON object with keys: "
    '"signal" ("BUY"|"SELL"|"HOLD"), "confidence" (integer 0-100), '
    '"summary" (1-3 plain sentences, no markdown). '
    "Do not include anything outside the JSON object."
)


@dataclass(frozen=True, slots=True)
class LLMResult:
    """Enhanced signal produced by DeepSeek (validated before return)."""

    signal: str  # BUY | SELL | HOLD
    confidence: float  # 0..100
    summary: str
    model: str


def _extract_json(text: str) -> dict[str, Any] | None:
    """Pull the first JSON object out of a chat response.

    Tolerates code fences and leading/trailing prose from the model.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


class DeepSeekClient:
    """Thin httpx wrapper around DeepSeek's chat-completions endpoint."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.deepseek_timeout), follow_redirects=True
        )

    def enabled(self) -> bool:
        return bool(self._settings.deepseek_api_key)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def enhance(self, context: dict[str, Any]) -> LLMResult | None:
        """Ask DeepSeek for a final signal; ``None`` on any problem."""
        if not self.enabled():
            return None
        payload = {
            "model": self._settings.deepseek_model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
        }
        try:
            response = await self._client.post(
                f"{self._settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._settings.deepseek_api_key}"},
                json=payload,
            )
            response.raise_for_status()
            body: Any = response.json()
            content = body["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.warning("DeepSeek call failed (%s); using deterministic signal", exc)
            return None

        parsed = _extract_json(content)
        signal = str(parsed.get("signal", "")).upper() if parsed else ""
        if signal not in {"BUY", "SELL", "HOLD"}:
            logger.warning("DeepSeek returned an invalid signal (%r); using deterministic signal", signal)
            return None
        try:
            confidence = float(parsed.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0
        summary = str(parsed.get("summary", "")).strip()
        return LLMResult(
            signal=signal,
            confidence=round(max(0.0, min(100.0, confidence)), 1),
            summary=summary or "AI summary unavailable.",
            model=self._settings.deepseek_model,
        )