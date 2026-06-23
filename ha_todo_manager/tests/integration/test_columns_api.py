"""Integration tests for /api/columns."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _board_id(client: TestClient) -> str:
    return client.get("/api/boards").json()[0]["id"]


@pytest.mark.integration
def test_list_columns_returns_seeded_defaults(client: TestClient) -> None:
    response = client.get("/api/columns")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    assert [c["status_key"] for c in data] == ["backlog", "todo", "in_progress", "done"]
    assert data[-1]["is_terminal"] is True


@pytest.mark.integration
def test_create_column(client: TestClient) -> None:
    response = client.post(
        "/api/columns",
        json={
            "board_id": _board_id(client),
            "name": "Review",
            "status_key": "review",
            "position": 4,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Review"
    assert body["status_key"] == "review"
    assert body["is_terminal"] is False


@pytest.mark.integration
def test_create_column_empty_name_rejected(client: TestClient) -> None:
    response = client.post("/api/columns", json={"name": "", "status_key": "x"})
    assert response.status_code == 422


@pytest.mark.integration
def test_patch_column_rename(client: TestClient) -> None:
    column_id = client.get("/api/columns").json()[0]["id"]
    response = client.patch(f"/api/columns/{column_id}", json={"name": "Renamed"})
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


@pytest.mark.integration
def test_patch_column_not_found(client: TestClient) -> None:
    response = client.patch("/api/columns/00000000-0000-0000-0000-000000000000", json={"name": "X"})
    assert response.status_code == 404


@pytest.mark.integration
def test_delete_column(client: TestClient) -> None:
    column_id = client.post(
        "/api/columns",
        json={"board_id": _board_id(client), "name": "Temp", "status_key": "temp"},
    ).json()["id"]
    response = client.delete(f"/api/columns/{column_id}")
    assert response.status_code == 204

    ids = [c["id"] for c in client.get("/api/columns").json()]
    assert column_id not in ids


@pytest.mark.integration
def test_delete_column_not_found(client: TestClient) -> None:
    response = client.delete("/api/columns/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.integration
def test_delete_column_with_todos_rejected(client: TestClient) -> None:
    column_id = client.get("/api/columns").json()[0]["id"]
    client.post("/api/todos", json={"title": "Blocks deletion", "column_id": column_id})

    response = client.delete(f"/api/columns/{column_id}")
    assert response.status_code == 422
