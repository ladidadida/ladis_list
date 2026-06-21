"""Database engine and session dependency."""

from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from .settings import get_settings

logger = logging.getLogger(__name__)

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(str(settings.db_url), echo=False)
    return _engine


def get_session() -> Generator[Session]:
    with Session(get_engine()) as session:
        yield session


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(get_engine())
