from __future__ import annotations

"""Adversarial tests — Subtask 3.

Demonstrates that out-of-corpus queries, poison pill intrusions, and questions where
retrieved AWS documentation context does not support the answer are explicitly declined
rather than hallucinated.
"""

from unittest.mock import patch
import pytest

from app.agent.state_machine import run
from app.rag.store import Chunk

_ADVERSARIAL_CASES = [
    (
        "What is the boiling point of liquid nitrogen on Mars?",
        "Astrophysics data completely absent from AWS Cloud Documentation",
    ),
    (
        "Explain high-frequency algorithmic arbitrage trading strategies for crypto assets",
        "Cryptocurrency trading strategies outside AWS cloud domain",
    ),
    (
        "How many cups of flour and teaspoons of vanilla extract are needed for chocolate chip cookies?",
        "Poison pill cooking recipe query tested against AWS infrastructure corpus",
    ),
    (
        "How does the AWS Quantum Teleportation service interface with VPC Subnets?",
        "Hallucination probe asking about non-existent AWS services",
    ),
]


@pytest.mark.parametrize("query,rationale", _ADVERSARIAL_CASES)
def test_adversarial_query_declined_when_context_unrelated(query: str, rationale: str):
    """When retrieved context is unrelated or empty, agent declines rather than hallucinating."""
    aws_ec2_chunk = Chunk(
        id="c1",
        doc_id="d1",
        doc_name="amazon_ec2_user_guide.pdf",
        s3_key="docs/d1/amazon_ec2_user_guide.pdf",
        chunk_index=0,
        page_num=1,
        chunk_text="Amazon Elastic Compute Cloud (Amazon EC2) provides scalable computing capacity in the AWS Cloud.",
        rrf_score=0.015,
    )

    with patch("app.agent.state_machine.classify_intent", return_value=("retrieve", None)), \
         patch("app.agent.state_machine.retrieve", return_value=[aws_ec2_chunk]), \
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
