from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException

from app.agent.state_machine import run as agent_run
from app.logger import get_logger
from app.models.request import ChatRequest
from app.models.response import ChatMessage, ChatResponse, Citation, ThreadDetail, ThreadSummary
from app.storage.s3 import s3_client

log = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

# ── In-memory thread store ────────────────────────────────────────────────────
# Production note: replace with Redis or DynamoDB for persistence + horizontal scale.
# For this scope, a module-level dict is zero-infra and sufficient.

_threads: dict[str, dict[str, Any]] = {}

# ── Metrics counters (also used by /metrics endpoint) ────────────────────────
metrics: dict[str, Any] = defaultdict(float)
metrics["queries_total"] = 0
metrics["retrieval_queries"] = 0
metrics["declined_queries"] = 0
metrics["latency_sum_ms"] = 0.0
metrics["token_sum"] = 0


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    thread_id = body.thread_id or str(uuid.uuid4())

    # Initialise thread if new
    if thread_id not in _threads:
        _threads[thread_id] = {
            "thread_id": thread_id,
            "title": body.message[:60],
            "messages": [],
            "created_at": datetime.now(tz=timezone.utc),
            "updated_at": datetime.now(tz=timezone.utc),
        }

    # Bind thread context to all log events in this request
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(thread_id=thread_id)

    # Store user message
    user_msg_id = str(uuid.uuid4())
    _threads[thread_id]["messages"].append(
        {
            "id": user_msg_id,
            "role": "user",
            "content": body.message,
            "intent": None,
            "citations": [],
            "timestamp": datetime.now(tz=timezone.utc),
        }
    )

    # Run agent
    result = agent_run(query=body.message, query_id=user_msg_id[:8])

    # Build citations with fresh presigned URLs
    citations: list[Citation] = []
    for i, chunk in enumerate(result.chunks, start=1):
        try:
            url = s3_client.generate_presigned_url(chunk.s3_key)
        except Exception as exc:
            log.warning("presigned_url_failed", s3_key=chunk.s3_key, error=str(exc))
            url = ""
        citations.append(
            Citation(
                index=i,
                doc_name=chunk.doc_name,
                doc_id=chunk.doc_id,
                s3_key=chunk.s3_key,
                page_num=chunk.page_num,
                chunk_text=chunk.chunk_text[:500],  # snippet for modal header
                presigned_url=url,
            )
        )

    # Store assistant message
    assistant_msg_id = str(uuid.uuid4())
    _threads[thread_id]["messages"].append(
        {
            "id": assistant_msg_id,
            "role": "assistant",
            "content": result.answer,
            "intent": result.intent,
            "citations": [c.model_dump() for c in citations],
            "timestamp": datetime.now(tz=timezone.utc),
        }
    )
    _threads[thread_id]["updated_at"] = datetime.now(tz=timezone.utc)

    # Update metrics
    metrics["queries_total"] += 1
    metrics["latency_sum_ms"] += result.latency_ms
    metrics["token_sum"] += result.token_count
    if result.intent == "retrieve":
        metrics["retrieval_queries"] += 1
    if result.intent == "declined":
        metrics["declined_queries"] += 1

    return ChatResponse(
        thread_id=thread_id,
        message_id=assistant_msg_id,
        answer=result.answer,
        intent=result.intent,  # type: ignore[arg-type]
        citations=citations,
        latency_ms=round(result.latency_ms, 2),
        token_count=result.token_count,
    )


@router.get("/threads", response_model=list[ThreadSummary])
async def list_threads() -> list[ThreadSummary]:
    summaries = []
    for t in sorted(_threads.values(), key=lambda x: x["updated_at"], reverse=True):
        summaries.append(
            ThreadSummary(
                thread_id=t["thread_id"],
                title=t["title"],
                message_count=len(t["messages"]),
                created_at=t["created_at"],
                updated_at=t["updated_at"],
            )
        )
    return summaries


@router.get("/threads/{thread_id}", response_model=ThreadDetail)
async def get_thread(thread_id: str) -> ThreadDetail:
    thread = _threads.get(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    messages = [
        ChatMessage(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            intent=m.get("intent"),
            citations=[Citation(**c) for c in m.get("citations", [])],
            timestamp=m["timestamp"],
        )
        for m in thread["messages"]
    ]
    return ThreadDetail(thread_id=thread_id, title=thread["title"], messages=messages)
