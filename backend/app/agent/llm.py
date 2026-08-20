from __future__ import annotations

import json
import google.generativeai as genai

from app.config import settings
from app.logger import get_logger
from app.rag.store import Chunk

log = get_logger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

_DECLINE_TRIGGER = "DECLINE_OUT_OF_CORPUS"

_GROUNDED_SYSTEM = f"""You are a strict, grounded research assistant. Answer the user's question \
using ONLY the provided context chunks.

CRITICAL RULES:
1. Cite sources inline using [N] notation matching the context chunk number.
2. If the context does NOT contain the answer, or if the question is out-of-domain/unsupported by the context, do NOT guess, extrapolate, or hallucinate.
3. Instead, you MUST output the exact token: {_DECLINE_TRIGGER}
4. Never include outside knowledge when answering grounded questions."""

_DIRECT_SYSTEM = """You are a helpful and concise AI assistant. Answer the user's question clearly."""


class GeminiLLM:
    def __init__(self, model: str = settings.LLM_MODEL) -> None:
        self._model = genai.GenerativeModel(model_name=model)
        self.model_name = model

    def generate(self, system: str, user: str) -> tuple[str, int]:
        """Generate general response. Returns (text, token_count)."""
        response = self._model.generate_content(
            [
                {"role": "user", "parts": [f"<system>{system}</system>\n\n{user}"]},
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
        text = response.text or ""
        tokens = getattr(response.usage_metadata, "total_token_count", 0)
        return text, tokens

    def generate_grounded(self, query: str, chunks: list[Chunk]) -> tuple[str, int]:
        """Generate a grounded answer citing [N] sources or output DECLINE_OUT_OF_CORPUS."""
        if not chunks:
            return _DECLINE_TRIGGER, 0

        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            context_parts.append(
                f"[{i}] Source: {chunk.doc_name} (Page {chunk.page_num})\n{chunk.chunk_text}"
            )
        context_block = "\n\n---\n\n".join(context_parts)

        user_prompt = (
            f"Context:\n\n{context_block}\n\n"
            f"Question: {query}\n\n"
            f"Remember: If the context does not answer the question, reply ONLY with '{_DECLINE_TRIGGER}'."
        )
        return self.generate(_GROUNDED_SYSTEM, user_prompt)

    def classify_intent(self, query: str) -> dict:
        """Classify query intent with JSON output."""
        prompt = f"""Classify the user query into exactly one intent.

Query: {query}

Respond ONLY with valid JSON:
{{"intent": "<direct|retrieve|tool>", "tool_name": <null|"calculator"|"date">, "reasoning": "<short description>"}}

Rules:
- "direct"   → greetings, general knowledge, standard concepts
- "retrieve" → queries looking for specific document content, papers, research facts, or corpus information
- "tool"     → arithmetic calculations or requests for current date/time
"""
        response = self._model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                response_mime_type="application/json",
                max_output_tokens=256,
            ),
        )
        try:
            return json.loads(response.text or "{}")
        except Exception:
            return {"intent": "retrieve", "tool_name": None, "reasoning": "fallback"}


llm = GeminiLLM()
