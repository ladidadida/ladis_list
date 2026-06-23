"""Integration tests for /api/recurrence and recurrence wiring in /api/todos."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _columns(client: TestClient) -> list[dict]:
    return client.get("/api/columns").json()


@pytest.mark.integration
def test_create_recurring_todo_sets_next_due(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    response = client.post(
        "/api/todos",
        json={"title": "Take out trash", "column_id": column_id, "rrule": "FREQ=DAILY"},
    )
    assert response.status_code == 201
    assert response.json()["next_due"] is not None


@pytest.mark.integration
def test_create_todo_invalid_rrule_rejected(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    response = client.post(
        "/api/todos",
        json={"title": "Bad rrule", "column_id": column_id, "rrule": "NOT A VALID RRULE"},
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_clearing_rrule_clears_next_due(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    todo_id = client.post(
        "/api/todos",
        json={"title": "Was recurring", "column_id": column_id, "rrule": "FREQ=DAILY"},
    ).json()["id"]

    response = client.patch(f"/api/todos/{todo_id}", json={"rrule": None})
    assert response.status_code == 200
    assert response.json()["next_due"] is None


@pytest.mark.integration
def test_materialise_endpoint_with_nothing_due(client: TestClient) -> None:
    response = client.post("/api/recurrence/materialise")
    assert response.status_code == 200
    assert response.json() == {"materialised": 0}


@pytest.mark.integration
def test_complete_recurring_todo_spawns_next_instance(client: TestClient) -> None:
    column_id = _columns(client)[0]["id"]
    todo_id = client.post(
        "/api/todos",
        json={"title": "Water plants", "column_id": column_id, "rrule": "FREQ=DAILY"},
    ).json()["id"]

    response = client.post(f"/api/todos/{todo_id}/complete")
    assert response.status_code == 200

    all_todos = client.get("/api/todos").json()
    children = [t for t in all_todos if t["recurrence_parent_id"] == todo_id]
    assert len(children) == 1
    assert children[0]["title"] == "Water plants"
    assert children[0]["rrule"] == "FREQ=DAILY"


@pytest.mark.integration
def test_complete_non_recurring_todo_unaffected(client: TestClient) -> None:
    """Regression: completing a plain todo must not be affected by recurrence wiring."""
    column_id = _columns(client)[0]["id"]
    todo_id = client.post("/api/todos", json={"title": "One-off", "column_id": column_id}).json()[
        "id"
    ]

    response = client.post(f"/api/todos/{todo_id}/complete")
    assert response.status_code == 200

    all_todos = client.get("/api/todos").json()
    assert len(all_todos) == 1


@pytest.mark.integration
def test_completing_a_materialised_instance_does_not_spawn_again(client: TestClient) -> None:
    """Only the root recurring todo spawns a next instance, not its children."""
    column_id = _columns(client)[0]["id"]
    todo_id = client.post(
        "/api/todos",
        json={"title": "Daily chore", "column_id": column_id, "rrule": "FREQ=DAILY"},
    ).json()["id"]
    client.post(f"/api/todos/{todo_id}/complete")

    all_todos = client.get("/api/todos").json()
    child = next(t for t in all_todos if t["recurrence_parent_id"] == todo_id)

    response = client.post(f"/api/todos/{child['id']}/complete")
    assert response.status_code == 200

    all_todos_after = client.get("/api/todos").json()
    assert len(all_todos_after) == 2


@pytest.mark.integration
def test_recurrence_stays_on_same_board(client: TestClient) -> None:
    """Regression: materialising/completing a recurring todo must not move it onto a
    different board's columns."""
    second_board = client.post("/api/boards", json={"name": "Second"}).json()
    second_column_id = client.get(f"/api/columns?board_id={second_board['id']}").json()[0]["id"]
    todo_id = client.post(
        "/api/todos",
        json={
            "title": "Recurring on second board",
            "column_id": second_column_id,
            "rrule": "FREQ=DAILY",
        },
    ).json()["id"]

    client.post(f"/api/todos/{todo_id}/complete")

    second_board_columns = {
        c["id"] for c in client.get(f"/api/columns?board_id={second_board['id']}").json()
    }
    all_todos = client.get("/api/todos").json()
    child = next(t for t in all_todos if t["recurrence_parent_id"] == todo_id)
    assert child["column_id"] in second_board_columns
