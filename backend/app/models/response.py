from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    index: int
    doc_name: str
    doc_id: str
    s3_key: str
    page_num: int
    chunk_text: str
    presigned_url: str


class ChatMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    intent: Literal["direct", "retrieve", "tool", "declined"] | None = None
    citations: list[Citation] = Field(default_factory=list)
    timestamp: datetime


class ChatResponse(BaseModel):
    thread_id: str
    message_id: str
    answer: str
    intent: Literal["direct", "retrieve", "tool", "declined"]
    citations: list[Citation] = Field(default_factory=list)
    latency_ms: float
    token_count: int


class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ThreadDetail(BaseModel):
    thread_id: str
    title: str
    messages: list[ChatMessage]


class DocumentInfo(BaseModel):
    doc_id: str
    doc_name: str
    s3_key: str
    chunk_count: int
    ingested_at: datetime


class IngestResponse(BaseModel):
    doc_id: str
    doc_name: str
    s3_key: str
    chunk_count: int


class HealthResponse(BaseModel):
    status: str
    milvus_connected: bool
    s3_connected: bool
    bm25_loaded: bool


class MetricsResponse(BaseModel):
    queries_total: int
    retrieval_queries: int
    declined_queries: int
    avg_retrieval_latency_ms: float
    avg_token_count: float
    documents_ingested: int
