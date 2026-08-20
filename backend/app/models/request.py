from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    thread_id: str | None = Field(None, description="Existing thread ID; omit to create a new thread")
    message: str = Field(..., min_length=1, max_length=4096, description="User message")


class IngestRequest(BaseModel):
    """Used internally; file upload goes through multipart form."""
    pass
