"""Todo DB table model and request/response schemas.

Phase 3 adds `assignee_id` (needs Person) and `source`/`source_ref`. The latter two
are set internally depending on the creation entry point (browser API vs HA webhook)
and are intentionally not on `TodoCreate`/`TodoUpdate` — not user-settable.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import ClassVar, Literal

from sqlmodel import Field, SQLModel

TodoSource = Literal["manual", "ha_webhook"]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class TodoBase(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    column_id: uuid.UUID = Field(foreign_key="column.id")
    assignee_id: uuid.UUID | None = Field(default=None, foreign_key="person.id")
    due_date: date | None = None
    priority: int = Field(default=0, ge=0, le=3)
    position: int = 0
    rrule: str | None = None


class TodoDB(TodoBase, table=True):
    __tablename__: ClassVar[str] = "todo"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    # Server-managed recurrence bookkeeping — not user-settable directly.
    next_due: date | None = None
    recurrence_parent_id: uuid.UUID | None = Field(default=None, foreign_key="todo.id")
    # Server-managed provenance — not user-settable directly. Plain `str` here (not
    # `TodoSource`) because SQLModel can't map a `Literal` type to a SQL column; the
    # `Literal` typing is still enforced where it matters, on `TodoRead`.
    source: str = "manual"
    source_ref: str | None = None


class TodoCreate(TodoBase):
    tag_ids: list[uuid.UUID] = []


class TodoUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    column_id: uuid.UUID | None = None
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None
    priority: int | None = Field(default=None, ge=0, le=3)
    position: int | None = None
    rrule: str | None = None
    tag_ids: list[uuid.UUID] | None = None


class TodoRead(TodoBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    next_due: date | None
    recurrence_parent_id: uuid.UUID | None
    source: TodoSource
    source_ref: str | None
    tag_ids: list[uuid.UUID]
