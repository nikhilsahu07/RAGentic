from __future__ import annotations

from unittest.mock import patch
import pytest

from app.rag.store import Chunk


def _rrf_formula(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank + 1)


def test_rrf_monotonicity():
    """RRF score should decrease monotonically with rank."""
    scores = [_rrf_formula(r) for r in range(5)]
    for i in range(len(scores) - 1):
        assert scores[i] > scores[i + 1]


def test_rrf_multi_list_fusion():
    """A document appearing in both dense and sparse lists gets a higher score."""
    k = 60
    # Document in both lists at rank 0
    fused_score = _rrf_formula(0, k) + _rrf_formula(0, k)
    # Document in only one list at rank 0
    single_score = _rrf_formula(0, k)
    assert fused_score > single_score


def test_retriever_pipeline():
    """Retriever combines dense and native BM25 search over Milvus chunks for AWS services."""
    fake_chunks = [
        Chunk(
            id="c1",
            doc_id="d1",
            doc_name="amazon_vpc_user_guide.pdf",
            s3_key="docs/d1/amazon_vpc_user_guide.pdf",
            chunk_index=0,
            page_num=1,
            chunk_text="Amazon Virtual Private Cloud (Amazon VPC) enables you to launch AWS resources into a virtual network.",
            rrf_score=0.0327,
        ),
        Chunk(
            id="c2",
            doc_id="d1",
            doc_name="amazon_vpc_user_guide.pdf",
            s3_key="docs/d1/amazon_vpc_user_guide.pdf",
            chunk_index=1,
            page_num=2,
            chunk_text="A subnet is a range of IP addresses in your VPC. Subnets can be public or private.",
            rrf_score=0.0163,
        ),
    ]

    with patch("app.rag.retriever.embedder") as mock_emb, \
         patch("app.rag.retriever.store") as mock_store:

        mock_emb.embed_query.return_value = [0.05] * 3072
        mock_store.hybrid_search_native.return_value = fake_chunks

        from app.rag.retriever import retrieve
        results = retrieve("how do VPC subnets work", top_n=5)

    assert len(results) > 0
    assert results[0].doc_name == "amazon_vpc_user_guide.pdf"
