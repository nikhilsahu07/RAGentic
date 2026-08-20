from __future__ import annotations

from app.config import settings
from app.logger import get_logger
from app.rag.embedder import embedder
from app.rag.store import Chunk, store

log = get_logger(__name__)


def retrieve(query: str, top_n: int = 5) -> list[Chunk]:
    """Native Milvus Hybrid Retrieval: Dense (Gemini embeddings) + Sparse (Native Milvus BM25 vectors)

    Both dense and sparse vector searches execute natively inside Milvus and are fused using
    Milvus's native RRFRanker(k=60).
    """
    try:
        # 1. Generate dense query embedding vector
        query_vec = embedder.embed_query(query)

        # 2. Execute Milvus Native Hybrid Search (Dense AnnSearch + BM25 AnnSearch + RRFRanker)
        chunks = store.hybrid_search_native(
            query_text=query,
            dense_vec=query_vec,
            top_k=top_n,
            k=settings.RRF_K,
        )

        log.debug(
            "native_milvus_hybrid_search_complete",
            query_preview=query[:60],
            returned_chunks=len(chunks),
        )
        return chunks
    except Exception as exc:
        log.error("retrieval_error", error=str(exc))
        return []
