"""FastAPI application factory.

Skeleton only — no routers are wired up yet. See AGENTS.md § API Design and
spec/roadmap.md for what lands here next.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import create_db_and_tables

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    create_db_and_tables()
    logger.info("ha-todo-manager started.")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ha-todo-manager",
        version="0.1.0",
        lifespan=_lifespan,
    )

    @app.get("/api/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
