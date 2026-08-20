from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pymilvus import (
    AnnSearchRequest,
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    RRFRanker,
    connections,
    utility,
)

from app.config import settings
from app.logger import get_logger

log = get_logger(__name__)

EMBEDDING_DIM = 3072  # gemini-embedding-001 dimension


@dataclass
class Chunk:
    """A retrieved document chunk with full metadata."""

    id: str
    doc_id: str
    doc_name: str
    s3_key: str
    chunk_index: int
    page_num: int
    chunk_text: str
    rrf_score: float = 0.0


def _build_schema() -> CollectionSchema:
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="s3_key", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="page_num", dtype=DataType.INT64),
        FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
    ]
    return CollectionSchema(
        fields=fields,
        description="RAGentic document chunks with dense and metadata fields",
        enable_dynamic_field=True,
    )


class MilvusStore:
    """Milvus client wrapper for collection management, vector upsert, and native hybrid search."""

    def __init__(self) -> None:
        self._collection: Collection | None = None

    def connect(self) -> None:
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )
        log.info(
            "milvus_connected",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        name = settings.MILVUS_COLLECTION
        if not utility.has_collection(name):
            schema = _build_schema()
            self._collection = Collection(name=name, schema=schema)
            index_params = {
                "metric_type": "IP",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            self._collection.create_index(field_name="embedding", index_params=index_params)
            log.info("milvus_collection_created", collection=name)
        else:
            self._collection = Collection(name=name)

        self._collection.load()

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            raise RuntimeError("MilvusStore not connected. Call connect() first.")
        return self._collection

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> None:
        """Insert or update chunks."""
        if not chunks:
            return
        data: dict[str, list] = {
            "id": [],
            "doc_id": [],
            "doc_name": [],
            "s3_key": [],
            "chunk_index": [],
            "page_num": [],
            "chunk_text": [],
            "embedding": [],
        }
        for c in chunks:
            for key in data:
                data[key].append(c[key])

        self.collection.upsert(list(data.values()))
        self.collection.flush()
        log.info("milvus_upsert_success", count=len(chunks))

    def search_dense(self, query_vec: list[float], top_k: int) -> list[tuple[str, float]]:
        """Return list of (chunk_id, score) sorted descending."""
        results = self.collection.search(
            data=[query_vec],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": 16}},
            limit=top_k,
            output_fields=["id"],
        )
        if not results:
            return []
        hits = results[0]
        return [(hit.entity.get("id"), hit.distance) for hit in hits]

    def hybrid_search_native(
        self,
        dense_vec: list[float],
        top_k: int = 5,
        k: int = 60,
    ) -> list[Chunk]:
        """Perform native Milvus multi-vector / hybrid search using RRFRanker(k=60)."""
        output_fields = [
            "id",
            "doc_id",
            "doc_name",
            "s3_key",
            "chunk_index",
            "page_num",
            "chunk_text",
        ]
        
        dense_req = AnnSearchRequest(
            data=[dense_vec],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": 16}},
            limit=top_k * 2,
        )

        # Milvus native RRFRanker for multi-request fusion
        reranker = RRFRanker(k=k)
        
        try:
            results = self.collection.hybrid_search(
                reqs=[dense_req],
                rerank=reranker,
                limit=top_k,
                output_fields=output_fields,
            )
            chunks: list[Chunk] = []
            if results and len(results) > 0:
                for hit in results[0]:
                    entity = hit.entity
                    chunks.append(
                        Chunk(
                            id=entity.get("id"),
                            doc_id=entity.get("doc_id"),
                            doc_name=entity.get("doc_name"),
                            s3_key=entity.get("s3_key"),
                            chunk_index=entity.get("chunk_index"),
                            page_num=entity.get("page_num"),
                            chunk_text=entity.get("chunk_text"),
                            rrf_score=hit.distance,
                        )
                    )
            return chunks
        except Exception as exc:
            log.warning("milvus_hybrid_search_fallback", error=str(exc))
            # Fallback to standard dense search + ID hydration
            dense_hits = self.search_dense(dense_vec, top_k=top_k)
            ids = [hit[0] for hit in dense_hits]
            return self.fetch_chunks_by_ids(ids)

    def fetch_chunks_by_ids(self, ids: list[str]) -> list[Chunk]:
        """Fetch full chunk records by primary key list."""
        if not ids:
            return []
        id_filter = ", ".join(f'"{i}"' for i in ids)
        expr = f"id in [{id_filter}]"
        rows = self.collection.query(
            expr=expr,
            output_fields=[
                "id",
                "doc_id",
                "doc_name",
                "s3_key",
                "chunk_index",
                "page_num",
                "chunk_text",
            ],
        )
        row_map = {r["id"]: r for r in rows}
        chunks: list[Chunk] = []
        for chunk_id in ids:
            if chunk_id in row_map:
                r = row_map[chunk_id]
                chunks.append(
                    Chunk(
                        id=r["id"],
                        doc_id=r["doc_id"],
                        doc_name=r["doc_name"],
                        s3_key=r["s3_key"],
                        chunk_index=r["chunk_index"],
                        page_num=r["page_num"],
                        chunk_text=r["chunk_text"],
                    )
                )
        return chunks

    def fetch_all_chunks(self) -> list[dict[str, Any]]:
        """Fetch all chunks for text/metadata retrieval."""
        try:
            return self.collection.query(
                expr="chunk_index >= 0",
                output_fields=["id", "chunk_text", "doc_name", "s3_key", "page_num", "doc_id", "chunk_index"],
                limit=16384,
            )
        except Exception:
            return []

    def list_documents(self) -> list[dict[str, Any]]:
        """Return one record per unique doc_id."""
        try:
            return self.collection.query(
                expr="chunk_index == 0",
                output_fields=["doc_id", "doc_name", "s3_key"],
                limit=1000,
            )
        except Exception:
            return []

    def is_connected(self) -> bool:
        try:
            return self._collection is not None and utility.has_collection(settings.MILVUS_COLLECTION)
        except Exception:
            return False


# Singleton instance
store = MilvusStore()
