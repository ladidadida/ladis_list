"""Integration tests for /api/persons."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import ha_todo_manager.ha_client as ha_client


@pytest.mark.integration
def test_list_persons_empty(client: TestClient) -> None:
    response = client.get("/api/persons")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration
def test_sync_persons(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch_persons() -> list[ha_client.PersonInfo]:
        return [
            {
                "ha_user_id": "abc123",
                "ha_person_entity_id": "person.slarti",
                "display_name": "Slarti",
                "avatar_url": None,
            }
        ]

    monkeypatch.setattr(ha_client, "fetch_persons", fake_fetch_persons)

    response = client.post("/api/persons/sync")
    assert response.status_code == 200
    assert response.json() == {"synced": 1}

    persons = client.get("/api/persons").json()
    assert len(persons) == 1
    assert persons[0]["display_name"] == "Slarti"
    assert persons[0]["ha_person_entity_id"] == "person.slarti"


@pytest.mark.integration
def test_sync_persons_upserts_on_second_call(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_fetch_persons() -> list[ha_client.PersonInfo]:
        return [
            {
                "ha_user_id": "abc123",
                "ha_person_entity_id": "person.slarti",
                "display_name": "Slarti Updated",
                "avatar_url": None,
            }
        ]

    monkeypatch.setattr(ha_client, "fetch_persons", fake_fetch_persons)

    client.post("/api/persons/sync")
    client.post("/api/persons/sync")

    persons = client.get("/api/persons").json()
    assert len(persons) == 1
    assert persons[0]["display_name"] == "Slarti Updated"


@pytest.mark.integration
def test_sync_persons_supervisor_unreachable_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import httpx

    async def fake_fetch_persons() -> list[ha_client.PersonInfo]:
        raise httpx.ConnectError("no route to host")

    monkeypatch.setattr(ha_client, "fetch_persons", fake_fetch_persons)

    response = client.post("/api/persons/sync")
    assert response.status_code == 503


@pytest.mark.integration
def test_create_person_manually(client: TestClient) -> None:
    response = client.post("/api/persons", json={"display_name": "Guest"})
    assert response.status_code == 201
    body = response.json()
    assert body["display_name"] == "Guest"
    assert body["ha_user_id"] is None
    assert body["ha_person_entity_id"] is None


@pytest.mark.integration
def test_create_person_empty_name_rejected(client: TestClient) -> None:
    response = client.post("/api/persons", json={"display_name": ""})
    assert response.status_code == 422


@pytest.mark.integration
def test_delete_person(client: TestClient) -> None:
    person_id = client.post("/api/persons", json={"display_name": "Temp"}).json()["id"]
    response = client.delete(f"/api/persons/{person_id}")
    assert response.status_code == 204

    ids = [p["id"] for p in client.get("/api/persons").json()]
    assert person_id not in ids


@pytest.mark.integration
def test_delete_person_not_found(client: TestClient) -> None:
    response = client.delete("/api/persons/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.integration
def test_delete_person_unassigns_todos(client: TestClient) -> None:
    person_id = client.post("/api/persons", json={"display_name": "Assignee"}).json()["id"]
    column_id = client.get("/api/columns").json()[0]["id"]
    todo_id = client.post(
        "/api/todos",
        json={"title": "Assigned", "column_id": column_id, "assignee_id": person_id},
    ).json()["id"]

    response = client.delete(f"/api/persons/{person_id}")
    assert response.status_code == 204

    todo = client.get(f"/api/todos/{todo_id}").json()
    assert todo["assignee_id"] is None
