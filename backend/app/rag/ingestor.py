from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.logger import get_logger
from app.rag.embedder import embedder
from app.rag.store import store
from app.storage.s3 import s3_client

log = get_logger(__name__)

# Recursive character text splitter with overlap
_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def ingest_document(file_path: str, original_filename: str) -> dict[str, Any]:
    """Ingest a PDF document into S3 and Milvus.

    Steps:
    1. Load PDF pages
    2. Chunk with overlap (800 chars, 150 overlap)
    3. Upload raw PDF to S3 under docs/{doc_id}/{filename}
    4. Generate 3072-dim embeddings via Gemini
    5. Upsert chunks into Milvus with s3_key, metadata, and embeddings
    """
    doc_id = str(uuid.uuid4())
    s3_key = f"docs/{doc_id}/{original_filename}"

    log.info("ingest_start", doc_id=doc_id, filename=original_filename, s3_key=s3_key)

    # 1. Load PDF
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    log.debug("ingest_pdf_loaded", doc_id=doc_id, pages=len(pages))

    # 2. Chunk
    chunks = _SPLITTER.split_documents(pages)
    log.debug("ingest_chunked", doc_id=doc_id, chunks=len(chunks))

    if not chunks:
        log.warning("ingest_no_text_extracted", filename=original_filename)
        return {"doc_id": doc_id, "doc_name": original_filename, "s3_key": s3_key, "chunk_count": 0}

    # 3. Upload raw PDF to S3
    try:
        s3_client.upload_file(local_path=file_path, s3_key=s3_key)
        log.info("ingest_s3_uploaded", doc_id=doc_id, s3_key=s3_key)
    except Exception as exc:
        log.error("ingest_s3_upload_failed", doc_id=doc_id, error=str(exc))

    # 4. Embed
    texts = [c.page_content for c in chunks]
    embeddings = embedder.embed_documents(texts)
    log.debug("ingest_embedded", doc_id=doc_id, count=len(embeddings))

    # 5. Build records for Milvus
    records = []
    for idx, (chunk, vec) in enumerate(zip(chunks, embeddings)):
        page_num = chunk.metadata.get("page", 0)
        if isinstance(page_num, int):
            page_num = page_num + 1  # 1-indexed for display
        records.append(
            {
                "id": f"{doc_id}_chunk_{idx}",
                "doc_id": doc_id,
                "doc_name": original_filename,
                "s3_key": s3_key,
                "chunk_index": idx,
                "page_num": int(page_num),
                "chunk_text": chunk.page_content[:65000],
                "embedding": vec,
            }
        )

    store.upsert_chunks(records)
    log.info("ingest_complete", doc_id=doc_id, chunk_count=len(records), s3_key=s3_key)

    return {
        "doc_id": doc_id,
        "doc_name": original_filename,
        "s3_key": s3_key,
        "chunk_count": len(records),
    }
