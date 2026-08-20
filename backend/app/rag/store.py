from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pymilvus import (
    AnnSearchRequest,
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    Function,
    FunctionType,
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
        FieldSchema(
            name="chunk_text",
            dtype=DataType.VARCHAR,
            max_length=65535,
            enable_analyzer=True,
            enable_match=True,
        ),
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
    ]

    schema = CollectionSchema(
        fields=fields,
        description="RAGentic document chunks with dense and native BM25 sparse vectors",
        enable_dynamic_field=True,
    )

    # Built-in BM25 function: automatically tokenizes chunk_text into sparse_vector on upsert
    bm25_fn = Function(
        name="text_bm25_fn",
        function_type=FunctionType.BM25,
        input_field_names=["chunk_text"],
        output_field_names=["sparse_vector"],
    )
    schema.add_function(bm25_fn)
    return schema


class MilvusStore:
    """Milvus client wrapper for collection management, native BM25 sparse generation, and native hybrid search."""

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
            
            # 1. Index on dense embedding
            dense_index_params = {
                "metric_type": "IP",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            self._collection.create_index(field_name="embedding", index_params=dense_index_params)
            
            # 2. Native BM25 Sparse Inverted Index
            sparse_index_params = {
                "metric_type": "BM25",
                "index_type": "SPARSE_INVERTED_INDEX",
                "params": {"drop_ratio_build": 0.0},
            }
            self._collection.create_index(field_name="sparse_vector", index_params=sparse_index_params)
            
            log.info("milvus_collection_and_bm25_indexes_created", collection=name)
        else:
            self._collection = Collection(name=name)

        self._collection.load()

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            self.connect()
        return self._collection

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> None:
        """Insert or update chunks. Milvus automatically derives sparse_vector from chunk_text."""
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

    def hybrid_search_native(
        self,
        query_text: str,
        dense_vec: list[float],
        top_k: int = 5,
        k: int = 60,
    ) -> list[Chunk]:
        """Perform native Milvus hybrid search (Dense embedding + Native BM25 sparse_vector) with RRFRanker(k=60)."""
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

        sparse_req = AnnSearchRequest(
            data=[query_text],
            anns_field="sparse_vector",
            param={"metric_type": "BM25", "params": {}},
            limit=top_k * 2,
        )

        reranker = RRFRanker(k=k)

        try:
            results = self.collection.hybrid_search(
                reqs=[dense_req, sparse_req],
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
            # Fallback to standard dense search
            search_res = self.collection.search(
                data=[dense_vec],
                anns_field="embedding",
                param={"metric_type": "IP", "params": {"nprobe": 16}},
                limit=top_k,
                output_fields=output_fields,
            )
            chunks = []
            if search_res and len(search_res) > 0:
                for hit in search_res[0]:
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
