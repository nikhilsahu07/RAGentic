from __future__ import annotations

import json
import google.generativeai as genai

from app.config import settings
from app.logger import get_logger
from app.rag.store import Chunk

log = get_logger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

_DECLINE_TRIGGER = "DECLINE_OUT_OF_CORPUS"

_AWS_GROUNDED_SYSTEM = f"""You are a specialized AWS Cloud Architecture & Infrastructure Assistant. \
Answer the user's question accurately using ONLY the provided AWS documentation context chunks.

CRITICAL RULES:
1. Cite source documentation chunks inline using [N] notation matching the respective context chunk number.
2. Ground all architecture designs, configuration parameters, IAM policies, and service behaviors strictly in the provided context.
3. If the provided context does NOT contain the necessary details to answer the question, or if the question is unrelated to the provided AWS documentation, do NOT guess, extrapolate, or hallucinate.
4. Instead, you MUST output the exact token: {_DECLINE_TRIGGER}
5. Never include outside assumptions or unsupported AWS claims not present in the context."""

_DIRECT_SYSTEM = """You are a helpful and concise AWS cloud engineer and AI assistant. Answer general questions clearly and concisely."""


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
        """Generate a grounded answer citing [N] sources from AWS documentation chunks."""
        if not chunks:
            return _DECLINE_TRIGGER, 0

        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            context_parts.append(
                f"[{i}] Source: {chunk.doc_name} (Page {chunk.page_num})\n{chunk.chunk_text}"
            )
        context_block = "\n\n---\n\n".join(context_parts)

        user_prompt = (
            f"AWS Documentation Context:\n\n{context_block}\n\n"
            f"User Question: {query}\n\n"
            f"Instructions: Provide a clear, technical answer citing sources as [1], [2], etc. "
            f"If the documentation above is insufficient to answer, respond ONLY with '{_DECLINE_TRIGGER}'."
        )
        return self.generate(_AWS_GROUNDED_SYSTEM, user_prompt)

    def classify_intent(self, query: str) -> dict:
        """Classify query intent with JSON output for AWS RAG."""
        prompt = f"""Classify the user query into exactly one intent for an AWS Cloud Services assistant.

Query: {query}

Respond ONLY with valid JSON:
{{"intent": "<direct|retrieve|tool>", "tool_name": <null|"calculator"|"date">, "reasoning": "<short description>"}}

Rules:
- "retrieve" → queries about AWS services (EC2, S3, ASG, IAM, CloudWatch, CloudFormation, ECR, ECS, Route 53, VPC, RDS, Lambda, Elastic IP, ELB, EBS), AWS architecture, CLI configs, pricing specs, or documentation facts
- "direct"   → general conversational greetings, basic programming syntax, non-cloud definitions
- "tool"     → arithmetic calculations (e.g. EC2 instance memory/cost math) or requests for current date/time
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
