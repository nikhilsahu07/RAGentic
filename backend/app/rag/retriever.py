from __future__ import annotations

from collections import defaultdict
import math
import re

from app.config import settings
from app.logger import get_logger
from app.rag.embedder import embedder
from app.rag.store import Chunk, store

log = get_logger(__name__)


def _tokenize(text: str) -> list[str]:
    """Simple alphanumeric tokenizer."""
    return re.findall(r"\w+", text.lower())


def _bm25_score(query_tokens: list[str], docs: list[dict], k1: float = 1.5, b: float = 0.75) -> list[tuple[str, float]]:
    """Compute BM25 scores over chunks retrieved from Milvus."""
    if not docs or not query_tokens:
        return []

    doc_tokens = [_tokenize(d["chunk_text"]) for d in docs]
    doc_lens = [len(tokens) for tokens in doc_tokens]
    avg_dl = sum(doc_lens) / max(len(doc_lens), 1)
    n_docs = len(docs)

    # Document frequency
    df: dict[str, int] = defaultdict(int)
    for tokens in doc_tokens:
        seen = set(tokens)
        for term in seen:
            df[term] += 1

    scores = []
    for i, tokens in enumerate(doc_tokens):
        score = 0.0
        dl = doc_lens[i]
        tf: dict[str, int] = defaultdict(int)
        for t in tokens:
            tf[t] += 1

        for q in query_tokens:
            if q in df:
                idf = math.log((n_docs - df[q] + 0.5) / (df[q] + 0.5) + 1.0)
                term_tf = tf[q]
                numerator = term_tf * (k1 + 1)
                denominator = term_tf + k1 * (1 - b + b * (dl / (avg_dl or 1.0)))
                score += idf * (numerator / denominator)

        scores.append((docs[i]["id"], score))

    scores.sort(key=lambda x: -x[1])
    return scores


def retrieve(query: str, top_n: int = 5) -> list[Chunk]:
    """Hybrid retrieval: Dense (Milvus IP) + Sparse (BM25) fused with Reciprocal Rank Fusion (RRF).

    Formula: score(d) = sum(1 / (k + rank_i)) where k=60.
    """
    k = settings.RRF_K
    dense_top_k = settings.DENSE_TOP_K
    bm25_top_k = settings.BM25_TOP_K

    try:
        # 1. Dense search in Milvus
        query_vec = embedder.embed_query(query)
        dense_hits = store.search_dense(query_vec, top_k=dense_top_k)

        # 2. Sparse BM25 search over Milvus chunks
        all_chunks = store.fetch_all_chunks()
        query_tokens = _tokenize(query)
        sparse_hits = _bm25_score(query_tokens, all_chunks)[:bm25_top_k]

        # 3. Reciprocal Rank Fusion
        rrf_scores: dict[str, float] = defaultdict(float)
        for rank, (chunk_id, _) in enumerate(dense_hits):
            rrf_scores[chunk_id] += 1.0 / (k + rank + 1)

        for rank, (chunk_id, _) in enumerate(sparse_hits):
            rrf_scores[chunk_id] += 1.0 / (k + rank + 1)

        if not rrf_scores:
            return []

        # 4. Fetch top_n chunks
        top_ids = sorted(rrf_scores, key=lambda cid: -rrf_scores[cid])[:top_n]
        chunks = store.fetch_chunks_by_ids(top_ids)

        for chunk in chunks:
            chunk.rrf_score = rrf_scores.get(chunk.id, 0.0)
        chunks.sort(key=lambda c: -c.rrf_score)

        log.debug(
            "retriever_rrf_complete",
            query_preview=query[:60],
            candidates=len(rrf_scores),
            returned=len(chunks),
        )
        return chunks
    except Exception as exc:
        log.error("retrieval_error", error=str(exc))
        return []
