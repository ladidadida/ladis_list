"""Integration tests for /api/webhook (HA automation integration)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _columns(client: TestClient) -> list[dict]:
    return client.get("/api/columns").json()


@pytest.mark.integration
def test_get_webhook_secret_shown_once(client: TestClient) -> None:
    first = client.get("/api/webhook/secret")
    assert first.status_code == 200
    secret = first.json()["secret"]
    assert secret

    second = client.get("/api/webhook/secret")
    assert second.status_code == 404


@pytest.mark.integration
def test_webhook_create_with_wrong_secret_returns_404(client: TestClient) -> None:
    response = client.post("/api/webhook/ha/wrong-secret", json={"action": "create", "title": "X"})
    assert response.status_code == 404


@pytest.mark.integration
def test_webhook_create_todo(client: TestClient) -> None:
    secret = client.get("/api/webhook/secret").json()["secret"]

    response = client.post(
        f"/api/webhook/ha/{secret}",
        json={"action": "create", "title": "Trash day reminder", "source_ref": "automation.trash"},
    )
    assert response.status_code == 200
    todo_id = response.json()["id"]

    todo = client.get(f"/api/todos/{todo_id}").json()
    assert todo["title"] == "Trash day reminder"
    assert todo["source"] == "ha_webhook"
    assert todo["source_ref"] == "automation.trash"
    # default column_status_key is "todo"
    todo_column = next(c for c in _columns(client) if c["id"] == todo["column_id"])
    assert todo_column["status_key"] == "todo"


@pytest.mark.integration
def test_webhook_create_resolves_assignee(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ha_todo_manager.ha_client as ha_client

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
    client.post("/api/persons/sync")

    secret = client.get("/api/webhook/secret").json()["secret"]
    response = client.post(
        f"/api/webhook/ha/{secret}",
        json={
            "action": "create",
            "title": "Assigned task",
            "assignee_ha_person_entity_id": "person.slarti",
        },
    )
    assert response.status_code == 200
    todo = client.get(f"/api/todos/{response.json()['id']}").json()
    persons = client.get("/api/persons").json()
    assert todo["assignee_id"] == persons[0]["id"]


@pytest.mark.integration
def test_webhook_create_unknown_column_status_key_rejected(client: TestClient) -> None:
    secret = client.get("/api/webhook/secret").json()["secret"]
    response = client.post(
        f"/api/webhook/ha/{secret}",
        json={"action": "create", "title": "X", "column_status_key": "does_not_exist"},
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_webhook_create_targets_named_board(client: TestClient) -> None:
    second_board = client.post("/api/boards", json={"name": "Second"}).json()
    secret = client.get("/api/webhook/secret").json()["secret"]

    response = client.post(
        f"/api/webhook/ha/{secret}",
        json={"action": "create", "title": "On second board", "board_name": "Second"},
    )
    assert response.status_code == 200
    todo = client.get(f"/api/todos/{response.json()['id']}").json()
    second_board_todos = client.get(f"/api/todos?board_id={second_board['id']}").json()
    assert any(t["id"] == todo["id"] for t in second_board_todos)


@pytest.mark.integration
def test_webhook_create_unknown_board_name_rejected(client: TestClient) -> None:
    secret = client.get("/api/webhook/secret").json()["secret"]
    response = client.post(
        f"/api/webhook/ha/{secret}",
        json={"action": "create", "title": "X", "board_name": "Does Not Exist"},
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_webhook_complete_todo(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    todo_id = client.post("/api/todos", json={"title": "Finish me", "column_id": column_id}).json()[
        "id"
    ]

    secret = client.get("/api/webhook/secret").json()["secret"]
    response = client.post(
        f"/api/webhook/ha/{secret}", json={"action": "complete", "todo_id": todo_id}
    )
    assert response.status_code == 200

    done_column = next(c for c in _columns(client) if c["is_terminal"])
    todo = client.get(f"/api/todos/{todo_id}").json()
    assert todo["column_id"] == done_column["id"]


@pytest.mark.integration
def test_webhook_complete_missing_todo_id_rejected(client: TestClient) -> None:
    secret = client.get("/api/webhook/secret").json()["secret"]
    response = client.post(f"/api/webhook/ha/{secret}", json={"action": "complete"})
    assert response.status_code == 422
