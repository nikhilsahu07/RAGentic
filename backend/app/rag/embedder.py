from __future__ import annotations

from dataclasses import dataclass, field

import google.generativeai as genai

from app.config import settings
from app.logger import get_logger

log = get_logger(__name__)

# Configure Gemini once at module level
genai.configure(api_key=settings.GEMINI_API_KEY)

_EMBED_BATCH_SIZE = 100  # Gemini embedding API batch limit


@dataclass
class GeminiEmbedder:
    """Wraps google-generativeai embed_content for batch embedding.

    Uses gemini-embedding-001 which outputs 3072-dimensional vectors.
    task_type is switched between documents (ingest) and queries (retrieval).
    """

    model: str = field(default_factory=lambda: settings.EMBEDDING_MODEL)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of document chunks (ingest-time)."""
        return self._embed(texts, task_type="retrieval_document")

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string (query-time)."""
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        """Batch-embed texts, respecting API batch size limit."""
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _EMBED_BATCH_SIZE):
            batch = texts[i : i + _EMBED_BATCH_SIZE]
            log.debug("embedding_batch", batch_size=len(batch), task_type=task_type)
            result = genai.embed_content(
                model=self.model,
                content=batch,
                task_type=task_type,
            )
            # API returns list of embeddings when content is a list
            embeddings = result["embedding"]
            if isinstance(embeddings[0], float):
                # Single item returned as flat list
                all_embeddings.append(embeddings)
            else:
                all_embeddings.extend(embeddings)
        return all_embeddings


# Module-level singleton
embedder = GeminiEmbedder()
