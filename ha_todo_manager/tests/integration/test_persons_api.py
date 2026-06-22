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
