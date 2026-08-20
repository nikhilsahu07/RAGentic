from __future__ import annotations

from fastapi import APIRouter

from app.logger import get_logger
from app.models.response import HealthResponse, MetricsResponse
from app.rag.store import store
from app.storage.s3 import s3_client

log = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        milvus_connected=store.is_connected(),
        s3_connected=s3_client.is_connected(),
        bm25_loaded=True,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def metrics_endpoint() -> MetricsResponse:
    from app.api.chat import metrics

    total = int(metrics["queries_total"])
    retrieval = int(metrics["retrieval_queries"])
    declined = int(metrics["declined_queries"])
    latency_sum = float(metrics["latency_sum_ms"])
    token_sum = float(metrics["token_sum"])

    avg_latency = latency_sum / total if total > 0 else 0.0
    avg_tokens = token_sum / total if total > 0 else 0.0

    try:
        docs_ingested = len(store.list_documents())
    except Exception:
        docs_ingested = 0

    log.info(
        "metrics_polled",
        queries_total=total,
        avg_retrieval_latency_ms=round(avg_latency, 2),
        avg_token_count=round(avg_tokens, 2),
    )

    return MetricsResponse(
        queries_total=total,
        retrieval_queries=retrieval,
        declined_queries=declined,
        avg_retrieval_latency_ms=round(avg_latency, 2),
        avg_token_count=round(avg_tokens, 2),
        documents_ingested=docs_ingested,
    )
