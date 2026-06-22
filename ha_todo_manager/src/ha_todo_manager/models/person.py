"""Person DB table model and read schema.

No PersonCreate schema: persons are only ever created internally, either by HA person
sync (`services/persons.sync_persons`) or lazily on first request from a not-yet-seen
HA user (`services/persons.get_or_create_by_ha_user_id`) — never via a public POST.
"""

from __future__ import annotations

import uuid
from typing import ClassVar

from sqlmodel import Field, SQLModel


class PersonBase(SQLModel):
    display_name: str = Field(min_length=1, max_length=100)
    ha_user_id: str | None = None
    ha_person_entity_id: str | None = None
    avatar_url: str | None = None


class PersonDB(PersonBase, table=True):
    __tablename__: ClassVar[str] = "person"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ha_user_id: str | None = Field(default=None, unique=True)
    ha_person_entity_id: str | None = Field(default=None, unique=True)


class PersonRead(PersonBase):
    id: uuid.UUID
