"""Todo DB table model and request/response schemas.

Phase 1 scope only: no assignee (Phase 3, needs Person), no recurrence fields
(Phase 2), no source/source_ref (Phase 3, webhook-created todos) — see
spec/roadmap.md.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import ClassVar

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class TodoBase(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    column_id: uuid.UUID = Field(foreign_key="column.id")
    due_date: date | None = None
    priority: int = Field(default=0, ge=0, le=3)
    position: int = 0


class TodoDB(TodoBase, table=True):
    __tablename__: ClassVar[str] = "todo"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class TodoCreate(TodoBase):
    tag_ids: list[uuid.UUID] = []


class TodoUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    column_id: uuid.UUID | None = None
    due_date: date | None = None
    priority: int | None = Field(default=None, ge=0, le=3)
    position: int | None = None
    tag_ids: list[uuid.UUID] | None = None


class TodoRead(TodoBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    tag_ids: list[uuid.UUID]
