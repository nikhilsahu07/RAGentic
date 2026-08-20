from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from app.agent.llm import llm, _DECLINE_TRIGGER
from app.agent.router import classify_intent
from app.agent.tools import dispatch_tool
from app.logger import get_logger
from app.rag.retriever import retrieve
from app.rag.store import Chunk

log = get_logger(__name__)

State = Literal["ROUTING", "DIRECT", "RETRIEVE", "TOOL_CALL", "DECLINED", "DONE"]

_DECLINE_MESSAGE = (
    "I don't have reliable information about this in the indexed AWS documentation and knowledge base. "
    "Please ask questions related to the indexed AWS services and architecture documents."
)


@dataclass
class AgentResult:
    answer: str
    intent: Literal["direct", "retrieve", "tool", "declined"]
    chunks: list[Chunk] = field(default_factory=list)
    token_count: int = 0
    latency_ms: float = 0.0


def run(query: str, query_id: str | None = None) -> AgentResult:
    """Execute the agentic state machine for a query.

    States:
      ROUTING    → classify query intent
      DIRECT     → direct knowledge answer
      RETRIEVE   → hybrid search → LLM grounded generation (with DECLINE_OUT_OF_CORPUS check)
      TOOL_CALL  → dispatch to tool
      DECLINED   → explicit decline if context is insufficient or out of corpus
      DONE       → return AgentResult
    """
    query_id = query_id or str(uuid.uuid4())[:8]
    t_start = time.perf_counter()

    state: State = "ROUTING"
    intent = "retrieve"
    tool_name: str | None = None
    answer = ""
    chunks: list[Chunk] = []
    token_count = 0

    log.info("agent_start", query_id=query_id, query_preview=query[:80])

    while state != "DONE":
        match state:
            case "ROUTING":
                intent_raw, tool_name = classify_intent(query)
                log.info("agent_routing", query_id=query_id, intent=intent_raw, tool=tool_name)
                if intent_raw == "direct":
                    state = "DIRECT"
                elif intent_raw == "tool":
                    state = "TOOL_CALL"
                else:
                    state = "RETRIEVE"

            case "DIRECT":
                answer, token_count = llm.generate(
                    system="You are a helpful and concise AWS cloud engineer and AI assistant.",
                    user=query,
                )
                intent = "direct"
                state = "DONE"
                log.info("agent_direct_done", query_id=query_id, tokens=token_count)

            case "RETRIEVE":
                chunks = retrieve(query, top_n=5)
                if not chunks:
                    log.info("agent_no_chunks_found", query_id=query_id)
                    state = "DECLINED"
                else:
                    raw_answer, token_count = llm.generate_grounded(query, chunks)
                    if _DECLINE_TRIGGER in raw_answer:
                        log.info("agent_groundedness_declined_by_llm", query_id=query_id)
                        state = "DECLINED"
                    else:
                        answer = raw_answer
                        intent = "retrieve"
                        state = "DONE"
                        log.info(
                            "agent_retrieve_success",
                            query_id=query_id,
                            chunks=len(chunks),
                            tokens=token_count,
                        )

            case "TOOL_CALL":
                tool_result = dispatch_tool(tool_name or "date", query)
                answer = f"**Tool result:** {tool_result}"
                intent = "tool"
                state = "DONE"
                log.info("agent_tool_done", query_id=query_id, tool=tool_name, result=tool_result)

            case "DECLINED":
                answer = _DECLINE_MESSAGE
                intent = "declined"
                chunks = []
                state = "DONE"
                log.info("agent_declined_state", query_id=query_id)

    latency_ms = (time.perf_counter() - t_start) * 1000
    log.info(
        "agent_completed",
        query_id=query_id,
        intent=intent,
        latency_ms=round(latency_ms, 2),
        token_count=token_count,
    )

    return AgentResult(
        answer=answer,
        intent=intent,  # type: ignore[arg-type]
        chunks=chunks,
        token_count=token_count,
        latency_ms=latency_ms,
    )
