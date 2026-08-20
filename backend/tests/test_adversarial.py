from __future__ import annotations

"""Adversarial tests — Subtask 3.

Demonstrates that out-of-corpus queries and questions where retrieved context
does not support the answer are explicitly declined rather than hallucinated.
"""

from unittest.mock import patch
import pytest

from app.agent.state_machine import run
from app.rag.store import Chunk

_ADVERSARIAL_CASES = [
    (
        "What is the boiling point of liquid nitrogen on Mars?",
        "Astrophysics/planetary data not present in ML documents",
    ),
    (
        "Explain high-frequency algorithmic arbitrage trading strategies for crypto assets",
        "Cryptocurrency financial trading outside domain",
    ),
    (
        "What did Satya Nadella say in the 2024 leaked memo regarding AI acquisitions?",
        "Specific non-existent or unindexed memo",
    ),
]


@pytest.mark.parametrize("query,rationale", _ADVERSARIAL_CASES)
def test_adversarial_query_declined_when_context_unrelated(query: str, rationale: str):
    """When retrieved context is unrelated or empty, agent declines rather than hallucinating."""
    irrelevant_chunk = Chunk(
        id="c1",
        doc_id="d1",
        doc_name="attention_is_all_you_need.pdf",
        s3_key="docs/d1/attention_is_all_you_need.pdf",
        chunk_index=0,
        page_num=1,
        chunk_text="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
        rrf_score=0.015,
    )

    with patch("app.agent.state_machine.classify_intent", return_value=("retrieve", None)), \
         patch("app.agent.state_machine.retrieve", return_value=[irrelevant_chunk]), \
         patch("app.agent.state_machine.llm") as mock_llm:

        # LLM adheres to strict prompt and emits decline trigger
        mock_llm.generate_grounded.return_value = ("DECLINE_OUT_OF_CORPUS", 30)

        result = run(query)

    assert result.intent == "declined", (
        f"Query '{query}' ({rationale}) must result in 'declined' intent, got '{result.intent}'"
    )
    assert len(result.chunks) == 0, "Declined response must clear context chunks"
    assert "knowledge base" in result.answer.lower() or "reliable information" in result.answer.lower()


def test_adversarial_query_declined_on_empty_retrieval():
    """If no chunks are found at all, agent immediately declines."""
    with patch("app.agent.state_machine.classify_intent", return_value=("retrieve", None)), \
         patch("app.agent.state_machine.retrieve", return_value=[]):

        result = run("What is the recipe for chocolate chip cookies?")

    assert result.intent == "declined"
    assert "knowledge base" in result.answer.lower()
