#!/usr/bin/env python3
"""Corpus ingest script.

Usage:
    python scripts/ingest_corpus.py [--corpus-dir ./corpus]

Place your PDF files in the corpus/ directory, then run this script once.
It is idempotent: already-ingested documents (by filename) are skipped.

The script connects to Milvus and S3 using the same .env config as the app.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure the app package is importable when running from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings  # noqa: E402 — must be after sys.path insert
from app.logger import configure_logging, get_logger  # noqa: E402
from app.rag.ingestor import ingest_document  # noqa: E402
from app.rag.store import store  # noqa: E402
from app.storage.s3 import s3_client  # noqa: E402

configure_logging()
log = get_logger("ingest_corpus")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PDF corpus into RAGentic")
    parser.add_argument(
        "--corpus-dir",
        default=settings.CORPUS_DIR,
        help="Directory containing PDF files (default: ./corpus)",
    )
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir).resolve()
    if not corpus_dir.exists():
        print(f"[ERROR] Corpus directory not found: {corpus_dir}")
        sys.exit(1)

    pdf_files = sorted(corpus_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[WARN] No PDF files found in {corpus_dir}")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  RAGentic Corpus Ingest")
    print(f"  Found {len(pdf_files)} PDF(s) in {corpus_dir}")
    print(f"{'='*60}\n")

    # Connect services
    print("Connecting to Milvus...")
    store.connect()
    print("✓ Milvus connected\n")

    # Get already-ingested filenames to skip
    try:
        existing = store.list_documents()
        ingested_names = {d["doc_name"] for d in existing}
    except Exception:
        ingested_names = set()

    results = []
    for pdf_path in pdf_files:
        filename = pdf_path.name
        if filename in ingested_names:
            print(f"  [SKIP] {filename} — already ingested")
            results.append({"name": filename, "status": "skipped", "chunks": 0})
            continue

        print(f"  [INGEST] {filename} ...", end=" ", flush=True)
        t0 = time.perf_counter()
        try:
            result = ingest_document(file_path=str(pdf_path), original_filename=filename)
            elapsed = time.perf_counter() - t0
            print(f"✓ {result['chunk_count']} chunks ({elapsed:.1f}s)")
            results.append({"name": filename, "status": "ok", "chunks": result["chunk_count"]})
        except Exception as exc:
            print(f"✗ FAILED: {exc}")
            log.error("ingest_failed", filename=filename, error=str(exc))
            results.append({"name": filename, "status": "failed", "chunks": 0})

    # Summary table
    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    print(f"  {'Document':<40} {'Status':<10} {'Chunks':>6}")
    print(f"  {'-'*40} {'-'*10} {'-'*6}")
    for r in results:
        print(f"  {r['name']:<40} {r['status']:<10} {r['chunks']:>6}")
    print(f"{'='*60}\n")

    ok = sum(1 for r in results if r["status"] == "ok")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = sum(1 for r in results if r["status"] == "failed")
    print(f"  Ingested: {ok}  Skipped: {skipped}  Failed: {failed}\n")


if __name__ == "__main__":
    main()
