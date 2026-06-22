"""Integration tests for /api/todos."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _columns(client: TestClient) -> list[dict]:
    return client.get("/api/columns").json()


@pytest.mark.integration
def test_list_todos_empty(client: TestClient) -> None:
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration
def test_create_todo_minimal(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    response = client.post("/api/todos", json={"title": "Buy milk", "column_id": column_id})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["column_id"] == column_id
    assert body["priority"] == 0
    assert body["tag_ids"] == []


@pytest.mark.integration
def test_create_todo_invalid_priority_rejected(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    response = client.post(
        "/api/todos", json={"title": "Bad", "column_id": column_id, "priority": 9}
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_create_todo_with_tags(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    tag_id = client.post("/api/tags", json={"name": "home", "color": "#abc"}).json()["id"]
    response = client.post(
        "/api/todos",
        json={"title": "Tagged", "column_id": column_id, "tag_ids": [tag_id]},
    )
    assert response.status_code == 201
    assert response.json()["tag_ids"] == [tag_id]


@pytest.mark.integration
def test_get_todo_not_found(client: TestClient) -> None:
    response = client.get("/api/todos/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.integration
def test_patch_todo_move_column(client: TestClient) -> None:
    columns = _columns(client)
    todo_id = client.post(
        "/api/todos", json={"title": "Move me", "column_id": columns[0]["id"]}
    ).json()["id"]

    response = client.patch(f"/api/todos/{todo_id}", json={"column_id": columns[1]["id"]})
    assert response.status_code == 200
    assert response.json()["column_id"] == columns[1]["id"]


@pytest.mark.integration
def test_patch_todo_replaces_tags(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    tag_a = client.post("/api/tags", json={"name": "a", "color": "#a"}).json()["id"]
    tag_b = client.post("/api/tags", json={"name": "b", "color": "#b"}).json()["id"]
    todo_id = client.post(
        "/api/todos", json={"title": "Retag", "column_id": column_id, "tag_ids": [tag_a]}
    ).json()["id"]

    response = client.patch(f"/api/todos/{todo_id}", json={"tag_ids": [tag_b]})
    assert response.status_code == 200
    assert response.json()["tag_ids"] == [tag_b]


@pytest.mark.integration
def test_patch_todo_not_found(client: TestClient) -> None:
    response = client.patch("/api/todos/00000000-0000-0000-0000-000000000000", json={"title": "X"})
    assert response.status_code == 404


@pytest.mark.integration
def test_delete_todo(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    todo_id = client.post("/api/todos", json={"title": "Remove", "column_id": column_id}).json()[
        "id"
    ]

    response = client.delete(f"/api/todos/{todo_id}")
    assert response.status_code == 204
    assert client.get(f"/api/todos/{todo_id}").status_code == 404


@pytest.mark.integration
def test_filter_todos_by_column(client: TestClient) -> None:
    columns = _columns(client)
    client.post("/api/todos", json={"title": "In backlog", "column_id": columns[0]["id"]})
    client.post("/api/todos", json={"title": "In todo", "column_id": columns[1]["id"]})

    response = client.get(f"/api/todos?column_id={columns[0]['id']}")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["In backlog"]


@pytest.mark.integration
def test_filter_todos_by_tag(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    tag_id = client.post("/api/tags", json={"name": "x", "color": "#x"}).json()["id"]
    client.post("/api/todos", json={"title": "Tagged", "column_id": column_id, "tag_ids": [tag_id]})
    client.post("/api/todos", json={"title": "Untagged", "column_id": column_id})

    response = client.get(f"/api/todos?tag_id={tag_id}")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Tagged"]


@pytest.mark.integration
def test_complete_todo_moves_to_terminal_column(client: TestClient) -> None:
    columns = _columns(client)
    todo_id = client.post(
        "/api/todos", json={"title": "Finish me", "column_id": columns[0]["id"]}
    ).json()["id"]

    response = client.post(f"/api/todos/{todo_id}/complete")
    assert response.status_code == 200
    done_column = next(c for c in columns if c["is_terminal"])
    assert response.json()["column_id"] == done_column["id"]


@pytest.mark.integration
def test_complete_todo_not_found(client: TestClient) -> None:
    response = client.post("/api/todos/00000000-0000-0000-0000-000000000000/complete")
    assert response.status_code == 404


@pytest.mark.integration
def test_filter_todos_by_assignee(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    # Resolve a Person id the cheap way: hit a route with X-Ingress-User so
    # get_current_user creates a stub Person, then assign a todo to it directly.
    client.get("/api/todos", headers={"X-Ingress-User": "user-1"})
    person_id = client.get("/api/persons").json()[0]["id"]

    assigned_id = client.post(
        "/api/todos",
        json={"title": "Assigned", "column_id": column_id, "assignee_id": person_id},
    ).json()["id"]
    client.post("/api/todos", json={"title": "Unassigned", "column_id": column_id})

    response = client.get(f"/api/todos?assignee_id={person_id}")
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert ids == [assigned_id]


@pytest.mark.integration
def test_mine_filter_resolves_current_user(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    client.get("/api/todos", headers={"X-Ingress-User": "user-2"})
    person_id = client.get("/api/persons").json()[0]["id"]

    mine_id = client.post(
        "/api/todos",
        json={"title": "Mine", "column_id": column_id, "assignee_id": person_id},
    ).json()["id"]
    client.post("/api/todos", json={"title": "Not mine", "column_id": column_id})

    response = client.get("/api/todos?mine=true", headers={"X-Ingress-User": "user-2"})
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert ids == [mine_id]


@pytest.mark.integration
def test_mine_filter_without_ingress_user_returns_empty(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    client.post("/api/todos", json={"title": "Anything", "column_id": column_id})

    response = client.get("/api/todos?mine=true")
    assert response.status_code == 200
    assert response.json() == []
