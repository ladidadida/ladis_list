"""Person DB table model and request/response schemas.

Persons are created three ways: HA person sync (`services/persons.sync_persons`),
lazily on first request from a not-yet-seen HA user
(`services/persons.get_or_create_by_ha_user_id`), or manually via `PersonCreate` for
people without an HA account (e.g. household members HA doesn't know about). Manual
persons have `ha_user_id`/`ha_person_entity_id` left `None`.
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


class PersonCreate(SQLModel):
    display_name: str = Field(min_length=1, max_length=100)
    avatar_url: str | None = None


class PersonRead(PersonBase):
    id: uuid.UUID
