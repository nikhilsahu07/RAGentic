from __future__ import annotations

from app.agent.llm import llm
from app.logger import get_logger

log = get_logger(__name__)

_FALLBACK_INTENT = "retrieve"


def classify_intent(query: str) -> tuple[str, str | None]:
    """Classify query intent using Gemini (JSON mode).

    Returns (intent, tool_name) where intent is one of:
      "direct"   — answer from model knowledge
      "retrieve" — answer from document corpus
      "tool"     — dispatch to a tool

    Falls back to "retrieve" on any parse or network error (conservative).
    """
    try:
        result = llm.classify_intent(query)
        intent = result.get("intent", _FALLBACK_INTENT)
        tool_name = result.get("tool_name")

        if intent not in ("direct", "retrieve", "tool"):
            log.warning("router_unknown_intent", intent=intent)
            intent = _FALLBACK_INTENT

        log.debug(
            "router_classified",
            intent=intent,
            tool_name=tool_name,
            reasoning=result.get("reasoning", ""),
        )
        return intent, tool_name

    except Exception as exc:
        log.error("router_error", error=str(exc))
        return _FALLBACK_INTENT, None
