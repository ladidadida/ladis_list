"""Shared pytest fixtures for ha_todo_manager tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine
from sqlmodel.pool import StaticPool

import ha_todo_manager.database as db_module
from ha_todo_manager.app import create_app


@pytest.fixture(name="engine")
def engine_fixture():
    """In-memory SQLite engine shared across the test via StaticPool."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    # Patch the module-level engine so lifespan helpers also use this engine.
    original = db_module._engine
    db_module._engine = test_engine
    yield test_engine
    db_module._engine = original
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(engine) -> Generator[TestClient]:
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
