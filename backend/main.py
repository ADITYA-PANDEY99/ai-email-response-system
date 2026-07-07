"""
FastAPI application entry point.

Production-grade setup with:
- Lifespan context manager for startup/shutdown
- CORS middleware
- Structured logging
- Health check endpoint
- OpenAPI documentation customization
"""
from __future__ import annotations

import logging
import logging.config
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.database import init_db
from backend.routers import analytics, dataset, emails, evaluate, generate

settings = get_settings()

# ── Logging configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle management."""
    logger.info("🚀 Starting %s v%s", settings.app_name, settings.app_version)

    # Initialize database tables
    await init_db()
    logger.info("✅ Database initialized")

    # Pre-warm embedding model (loads model into memory)
    try:
        from backend.retrieval.embedder import get_embedder
        get_embedder()
        logger.info("✅ Embedding model loaded")
    except Exception as e:
        logger.warning("⚠️  Embedding model failed to load: %s", e)

    # Initialize FAISS store (loads existing index if present)
    try:
        from backend.retrieval.faiss_store import get_faiss_store
        store = get_faiss_store()
        logger.info("✅ FAISS store initialized (size=%d)", store.size)
    except Exception as e:
        logger.warning("⚠️  FAISS store failed: %s", e)

    logger.info("🟢 Application ready at http://%s:%d", settings.host, settings.port)
    yield

    logger.info("🔴 Shutting down %s", settings.app_name)


# ── Application factory ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## AI Email Suggested Response System

A production-ready RAG pipeline that learns from historical email datasets
and generates evaluated, scored email responses using LLMs.

### Key Features
- **RAG Pipeline**: FAISS + sentence-transformers retrieval
- **Multi-metric Evaluation**: 12 weighted metrics beyond simple BLEU
- **Gemini Integration**: Primary LLM with automatic fallback
- **Real-time Scoring**: Per-response confidence scores and explanations
""",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    process_time = (time.monotonic() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.1f}"
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(emails.router)
app.include_router(generate.router)
app.include_router(evaluate.router)
app.include_router(dataset.router)
app.include_router(analytics.router)


# ── Health & info endpoints ───────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check() -> JSONResponse:
    """System health check."""
    from backend.retrieval.faiss_store import get_faiss_store
    store = get_faiss_store()
    return JSONResponse({
        "status": "healthy",
        "version": settings.app_version,
        "faiss_index_size": store.size,
        "gemini_configured": settings.has_gemini_key,
        "using_fallback": not settings.has_gemini_key,
    })


@app.get("/", tags=["system"])
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
