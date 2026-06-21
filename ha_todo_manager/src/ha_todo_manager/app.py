"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session, select

from .database import create_db_and_tables, get_engine
from .models.column import ColumnDB
from .routers import columns, tags, todos

logger = logging.getLogger(__name__)

_DEFAULT_COLUMNS: list[tuple[str, str, bool]] = [
    ("Backlog", "backlog", False),
    ("To Do", "todo", False),
    ("In Progress", "in_progress", False),
    ("Done", "done", True),
]


def _seed_default_columns() -> None:
    with Session(get_engine()) as session:
        existing = session.exec(select(ColumnDB)).first()
        if existing is not None:
            return
        for position, (name, status_key, is_terminal) in enumerate(_DEFAULT_COLUMNS):
            session.add(
                ColumnDB(
                    name=name, status_key=status_key, position=position, is_terminal=is_terminal
                )
            )
        session.commit()
    logger.info("Seeded %d default columns.", len(_DEFAULT_COLUMNS))


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    create_db_and_tables()
    _seed_default_columns()
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

    app.include_router(columns.router, prefix="/api")
    app.include_router(tags.router, prefix="/api")
    app.include_router(todos.router, prefix="/api")

    return app
