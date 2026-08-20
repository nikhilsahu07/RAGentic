from __future__ import annotations

import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse

from app.config import settings
from app.logger import get_logger
from app.models.response import DocumentInfo, IngestResponse
from app.rag.ingestor import ingest_document
from app.rag.store import store
from app.storage.s3 import s3_client

log = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Track ingested documents in-memory (mirrors Milvus chunk_index==0 records)
_documents: dict[str, dict] = {}


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    """Ingest a PDF document into the RAG pipeline."""
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    original_name = file.filename or f"document_{uuid.uuid4()}.pdf"
    log.info("ingest_upload_received", filename=original_name)

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


@router.get("/raw")
async def get_raw_pdf(key: str = Query(..., description="S3 key or document filename")) -> Response:
    """Stream PDF directly with inline content disposition for in-browser rendering."""
    doc_filename = Path(key).name
    local_path = Path(settings.CORPUS_DIR) / doc_filename

    # 1. Serve from local corpus if present
    if local_path.exists() and local_path.is_file():
        return FileResponse(
            path=str(local_path),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{doc_filename}"',
                "Access-Control-Allow-Origin": "*",
            },
        )

    # 2. Otherwise stream from S3 / MinIO
    try:
        obj = s3_client._client.get_object(Bucket=settings.S3_BUCKET, Key=key)
        return StreamingResponse(
            obj["Body"],
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{doc_filename}"',
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Document '{key}' could not be loaded: {exc}")


@router.get("", response_model=list[DocumentInfo])
async def list_documents() -> list[DocumentInfo]:
    """List all documents that have been ingested."""
    docs = []
    try:
        milvus_docs = store.list_documents()
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
