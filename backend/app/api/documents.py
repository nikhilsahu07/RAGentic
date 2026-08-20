from __future__ import annotations

import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.logger import get_logger
from app.models.response import DocumentInfo, IngestResponse
from app.rag.ingestor import ingest_document
from app.rag.store import store

log = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Track ingested documents in-memory (mirrors Milvus chunk_index==0 records)
_documents: dict[str, dict] = {}


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    """Ingest a PDF document into the RAG pipeline.

    Saves the upload to a temp file, runs the full ingest pipeline,
    then cleans up. Returns the doc_id, chunk count, and S3 key.
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    original_name = file.filename or f"document_{uuid.uuid4()}.pdf"
    log.info("ingest_upload_received", filename=original_name)

    # Write to a temp file for langchain's PyPDFLoader
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = ingest_document(file_path=tmp_path, original_filename=original_name)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    _documents[result["doc_id"]] = {
        **result,
        "ingested_at": datetime.now(tz=timezone.utc),
    }

    return IngestResponse(
        doc_id=result["doc_id"],
        doc_name=result["doc_name"],
        s3_key=result["s3_key"],
        chunk_count=result["chunk_count"],
    )


@router.get("", response_model=list[DocumentInfo])
async def list_documents() -> list[DocumentInfo]:
    """List all documents that have been ingested."""
    docs = []
    # Merge in-memory tracking with Milvus source of truth
    try:
        milvus_docs = store.list_documents()
        milvus_ids = {d["doc_id"] for d in milvus_docs}
        for d in milvus_docs:
            if d["doc_id"] not in _documents:
                _documents[d["doc_id"]] = {
                    "doc_id": d["doc_id"],
                    "doc_name": d["doc_name"],
                    "s3_key": d["s3_key"],
                    "chunk_count": 0,
                    "ingested_at": datetime.now(tz=timezone.utc),
                }
    except Exception as exc:
        log.warning("list_docs_milvus_error", error=str(exc))

    for doc in _documents.values():
        docs.append(
            DocumentInfo(
                doc_id=doc["doc_id"],
                doc_name=doc["doc_name"],
                s3_key=doc["s3_key"],
                chunk_count=doc.get("chunk_count", 0),
                ingested_at=doc["ingested_at"],
            )
        )
    return sorted(docs, key=lambda d: d.ingested_at, reverse=True)
