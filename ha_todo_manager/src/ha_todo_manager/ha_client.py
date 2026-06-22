"""Home Assistant Supervisor REST client.

`SUPERVISOR_TOKEN` and the Supervisor base URL are fixed runtime constants (see
AGENTS.md § Architecture) — HA injects the token automatically inside a real add-on
container, and the base URL never varies. Neither is a user-facing setting.
"""

from __future__ import annotations

import os
from typing import Any, TypedDict

import httpx

SUPERVISOR_BASE_URL = "http://supervisor/core/api"


class PersonInfo(TypedDict):
    ha_user_id: str | None
    ha_person_entity_id: str
    display_name: str
    avatar_url: str | None


def parse_person_state(state: dict[str, Any]) -> PersonInfo:
    """Pure mapping from a single HA `person.*` state object to our shape.

    Kept separate from the HTTP call so it's unit-testable without a network/Supervisor.
    """
    attributes = state.get("attributes", {})
    entity_id = state["entity_id"]
    return {
        "ha_user_id": attributes.get("user_id"),
        "ha_person_entity_id": entity_id,
        "display_name": attributes.get("friendly_name") or entity_id,
        "avatar_url": attributes.get("entity_picture"),
    }


async def fetch_persons() -> list[PersonInfo]:
    """Fetch and parse all `person.*` entities from the Supervisor's Core API."""
    token = os.environ.get("SUPERVISOR_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        base_url=SUPERVISOR_BASE_URL, headers=headers, timeout=10
    ) as client:
        response = await client.get("/states")
        response.raise_for_status()
        states = response.json()
    return [parse_person_state(s) for s in states if s.get("entity_id", "").startswith("person.")]
