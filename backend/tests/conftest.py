from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_store():
    with patch("app.rag.store.store") as m:
        yield m


@pytest.fixture
def mock_embedder():
    with patch("app.rag.embedder.embedder") as m:
        m.embed_query.return_value = [0.1] * 3072
        m.embed_documents.return_value = [[0.1] * 3072]
        yield m


@pytest.fixture
def mock_llm():
    with patch("app.agent.llm.llm") as m:
        m.generate.return_value = ("Mocked answer.", 100)
        m.generate_grounded.return_value = ("Grounded answer citing [1].", 150)
        m.classify_intent.return_value = {"intent": "retrieve", "tool_name": None, "reasoning": "test"}
        yield m
