"""Integration tests for the API key middleware."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import ha_shopping_list.database as db_module
from ha_shopping_list.app import create_app
from ha_shopping_list.database import get_session
from ha_shopping_list.settings import Settings

_TEST_KEY = "test-secret-key-1234"


@pytest.fixture(name="engine_for_apikey")
def engine_for_apikey_fixture():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    original = db_module._engine
    db_module._engine = test_engine
    yield test_engine
    db_module._engine = original
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="session_for_apikey")
def session_for_apikey_fixture(engine_for_apikey) -> Generator[Session]:
    with Session(engine_for_apikey) as session:
        yield session


@pytest.fixture(name="client_with_key")
def client_with_key_fixture(
    engine_for_apikey, session_for_apikey: Session
) -> Generator[TestClient]:
    """TestClient for an app instance that has api_key configured."""

    def override_get_session() -> Generator[Session]:
        yield session_for_apikey

    settings = Settings(api_key=_TEST_KEY)
    with patch("ha_shopping_list.app.get_settings", return_value=lambda: settings):
        with patch("ha_shopping_list.settings.get_settings", return_value=lambda: settings):
            # Patch at the module level where create_app reads settings
            import ha_shopping_list.app as app_module

            original_get_settings = app_module.get_settings
            app_module.get_settings = lambda: settings  # type: ignore[assignment]
            try:
                app = create_app()
                app.dependency_overrides[get_session] = override_get_session
                with TestClient(app, raise_server_exceptions=False) as client:
                    yield client
                app.dependency_overrides.clear()
            finally:
                app_module.get_settings = original_get_settings


@pytest.mark.integration
def test_api_key_missing_returns_401(client_with_key: TestClient) -> None:
    response = client_with_key.get("/api/v1/items")
    assert response.status_code == 401


@pytest.mark.integration
def test_api_key_wrong_returns_401(client_with_key: TestClient) -> None:
    response = client_with_key.get("/api/v1/items", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


@pytest.mark.integration
def test_api_key_correct_allows_access(client_with_key: TestClient) -> None:
    response = client_with_key.get("/api/v1/items", headers={"X-API-Key": _TEST_KEY})
    assert response.status_code == 200


@pytest.mark.integration
def test_ingress_path_header_bypasses_key(client_with_key: TestClient) -> None:
    """Requests arriving via HA Ingress carry X-Ingress-Path and need no API key."""
    response = client_with_key.get(
        "/api/v1/items", headers={"X-Ingress-Path": "/api/hassio_ingress/xxxx"}
    )
    assert response.status_code == 200


@pytest.mark.integration
def test_api_key_allows_post(client_with_key: TestClient) -> None:
    response = client_with_key.post(
        "/api/v1/items",
        json={"name": "Milk"},
        headers={"X-API-Key": _TEST_KEY},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Milk"


@pytest.mark.integration
def test_no_api_key_configured_allows_all(client: TestClient) -> None:
    """When api_key is empty, all requests pass through (existing behaviour)."""
    response = client.get("/api/v1/items")
    assert response.status_code == 200
