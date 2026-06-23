"""Integration tests for /api/boards."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_list_boards_returns_seeded_default(client: TestClient) -> None:
    response = client.get("/api/boards")
    assert response.status_code == 200
    boards = response.json()
    assert len(boards) == 1
    assert boards[0]["name"] == "Board"


@pytest.mark.integration
def test_create_board_seeds_default_columns(client: TestClient) -> None:
    response = client.post("/api/boards", json={"name": "Second Board"})
    assert response.status_code == 201
    board = response.json()
    assert board["name"] == "Second Board"

    columns = client.get(f"/api/columns?board_id={board['id']}").json()
    assert [c["status_key"] for c in columns] == ["backlog", "todo", "in_progress", "done"]


@pytest.mark.integration
def test_create_board_assigns_increasing_position(client: TestClient) -> None:
    second = client.post("/api/boards", json={"name": "Second"}).json()
    third = client.post("/api/boards", json={"name": "Third"}).json()

    boards = client.get("/api/boards").json()
    assert [b["name"] for b in boards] == ["Board", "Second", "Third"]
    assert second["position"] == 1
    assert third["position"] == 2


@pytest.mark.integration
def test_columns_scoped_per_board(client: TestClient) -> None:
    first_board_id = client.get("/api/boards").json()[0]["id"]
    second_board = client.post("/api/boards", json={"name": "Second"}).json()

    first_columns = client.get(f"/api/columns?board_id={first_board_id}").json()
    second_columns = client.get(f"/api/columns?board_id={second_board['id']}").json()
    assert len(first_columns) == 4
    assert len(second_columns) == 4
    # Both boards can have a column with the same status_key without colliding.
    assert {c["status_key"] for c in first_columns} == {c["status_key"] for c in second_columns}


@pytest.mark.integration
def test_todos_scoped_per_board(client: TestClient) -> None:
    first_board_id = client.get("/api/boards").json()[0]["id"]
    second_board = client.post("/api/boards", json={"name": "Second"}).json()
    second_column_id = client.get(f"/api/columns?board_id={second_board['id']}").json()[0]["id"]

    client.post("/api/todos", json={"title": "On second board", "column_id": second_column_id})

    first_board_todos = client.get(f"/api/todos?board_id={first_board_id}").json()
    second_board_todos = client.get(f"/api/todos?board_id={second_board['id']}").json()
    assert first_board_todos == []
    assert len(second_board_todos) == 1


@pytest.mark.integration
def test_rename_board(client: TestClient) -> None:
    board_id = client.get("/api/boards").json()[0]["id"]
    response = client.patch(f"/api/boards/{board_id}", json={"name": "Renamed"})
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


@pytest.mark.integration
def test_patch_board_not_found(client: TestClient) -> None:
    response = client.patch("/api/boards/00000000-0000-0000-0000-000000000000", json={"name": "X"})
    assert response.status_code == 404


@pytest.mark.integration
def test_cannot_delete_last_board(client: TestClient) -> None:
    board_id = client.get("/api/boards").json()[0]["id"]
    response = client.delete(f"/api/boards/{board_id}")
    assert response.status_code == 422


@pytest.mark.integration
def test_delete_board_cascades_columns_and_todos(client: TestClient) -> None:
    second_board = client.post("/api/boards", json={"name": "Second"}).json()
    second_column_id = client.get(f"/api/columns?board_id={second_board['id']}").json()[0]["id"]
    todo_id = client.post(
        "/api/todos", json={"title": "Goes away", "column_id": second_column_id}
    ).json()["id"]

    response = client.delete(f"/api/boards/{second_board['id']}")
    assert response.status_code == 204

    assert client.get(f"/api/todos/{todo_id}").status_code == 404
    assert client.get("/api/columns?board_id=" + second_board["id"]).json() == []
    board_ids = [b["id"] for b in client.get("/api/boards").json()]
    assert second_board["id"] not in board_ids


@pytest.mark.integration
def test_delete_board_not_found(client: TestClient) -> None:
    response = client.delete("/api/boards/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
