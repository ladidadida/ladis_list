"""Unit tests for ha_todo_manager.ha_client — pure HA state parsing, no network."""

from __future__ import annotations

from ha_todo_manager.ha_client import parse_person_state


def test_parse_person_state_full() -> None:
    state = {
        "entity_id": "person.slarti",
        "attributes": {
            "user_id": "abc123",
            "friendly_name": "Slarti",
            "entity_picture": "/api/image/serve/xyz",
        },
    }
    info = parse_person_state(state)
    assert info == {
        "ha_user_id": "abc123",
        "ha_person_entity_id": "person.slarti",
        "display_name": "Slarti",
        "avatar_url": "/api/image/serve/xyz",
    }


def test_parse_person_state_minimal_falls_back_to_entity_id() -> None:
    state = {"entity_id": "person.unnamed", "attributes": {}}
    info = parse_person_state(state)
    assert info["display_name"] == "person.unnamed"
    assert info["ha_user_id"] is None
    assert info["avatar_url"] is None
