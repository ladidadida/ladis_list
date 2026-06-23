"""Board DB table model and request/response schemas.

A board groups a set of columns (and, transitively, their todos). Tags and persons
stay global/shared across all boards — only columns (and therefore todos) are
board-scoped.
"""

from __future__ import annotations

import uuid
from typing import ClassVar

from sqlmodel import Field, SQLModel


class BoardBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    position: int = 0


class BoardDB(BoardBase, table=True):
    __tablename__: ClassVar[str] = "board"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class BoardCreate(BoardBase):
    pass


class BoardUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    position: int | None = None


class BoardRead(BoardBase):
    id: uuid.UUID
