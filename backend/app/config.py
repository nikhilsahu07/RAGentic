from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini
    GEMINI_API_KEY: str = "test-key"
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    LLM_MODEL: str = "gemini-2.5-flash"

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "ragentic_chunks"

    # S3 / MinIO
    S3_BUCKET: str = "ragentic-docs"
    S3_ENDPOINT_URL: str | None = None  # None → real AWS S3; set to http://minio:9000 for MinIO
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "minioadmin"
    AWS_SECRET_ACCESS_KEY: str = "minioadmin"

    # RAG Tuning
    BM25_TOP_K: int = 20
    DENSE_TOP_K: int = 20
    RRF_K: int = 60

    # Application
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"
    CORPUS_DIR: str = "./corpus"


settings = Settings()
