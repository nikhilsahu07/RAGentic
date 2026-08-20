from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, documents, health
from app.logger import configure_logging, get_logger
from app.rag.store import store
from app.storage.s3 import s3_client

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: initialize Milvus collection connection and verify S3."""
    log.info("startup_begin")

    try:
        store.connect()
    except Exception as exc:
        log.warning("startup_milvus_deferred", error=str(exc))

    log.info(
        "startup_complete",
        milvus_ok=store.is_connected(),
        s3_ok=s3_client.is_connected(),
    )

    yield

    log.info("shutdown")


app = FastAPI(
    title="RAGentic",
    description="Agentic RAG Microservice — hybrid retrieval, agentic routing, grounded answers with citations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(health.router)
