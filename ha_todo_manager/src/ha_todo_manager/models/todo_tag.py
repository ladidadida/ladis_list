"""TodoTag association table (many-to-many between Todo and Tag)."""

from __future__ import annotations

import uuid
from typing import ClassVar

from sqlmodel import Field, SQLModel


class TodoTagDB(SQLModel, table=True):
    __tablename__: ClassVar[str] = "todo_tag"

    todo_id: uuid.UUID = Field(foreign_key="todo.id", primary_key=True)
    tag_id: uuid.UUID = Field(foreign_key="tag.id", primary_key=True)
