"""Integration tests for /api/tags."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_list_tags_empty(client: TestClient) -> None:
    response = client.get("/api/tags")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration
def test_create_tag(client: TestClient) -> None:
    response = client.post("/api/tags", json={"name": "urgent", "color": "#ff0000"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "urgent"
    assert body["color"] == "#ff0000"


@pytest.mark.integration
def test_create_tag_empty_name_rejected(client: TestClient) -> None:
    response = client.post("/api/tags", json={"name": "", "color": "#fff"})
    assert response.status_code == 422


@pytest.mark.integration
def test_delete_tag(client: TestClient) -> None:
    tag_id = client.post("/api/tags", json={"name": "temp", "color": "#000"}).json()["id"]
    response = client.delete(f"/api/tags/{tag_id}")
    assert response.status_code == 204

    ids = [t["id"] for t in client.get("/api/tags").json()]
    assert tag_id not in ids


@pytest.mark.integration
def test_delete_tag_not_found(client: TestClient) -> None:
    response = client.delete("/api/tags/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
