"""FastAPI backend for the recommendation pipeline.

Run locally:
    uvicorn src.api.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from src.api.routes import router
from src.data.repository import get_repository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Load dataset on startup so health checks are meaningful."""
    settings = get_settings()
    repo = get_repository(settings=settings)
    try:
        repo.ensure_loaded()
        logger.info(
            "API startup: repository loaded (%s restaurants, %s cities)",
            repo.count(),
            len(repo.get_locations()),
        )
    except Exception as exc:  # noqa: BLE001
        # Keep app running so /health can report failure instead of crashing.
        logger.exception("API startup: failed to load repository: %s", exc)
    yield


app = FastAPI(
    title="Zomoto API",
    version="0.1.0",
    lifespan=lifespan,
)

# Optional: allow local UI / scripts to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, Any]:
    return {"name": "zomoto", "status": "ok", "docs": "/docs", "api_base": "/api/v1"}

