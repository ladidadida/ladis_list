"""Column DB table model and request/response schemas."""

from __future__ import annotations

import uuid
from typing import ClassVar

from sqlmodel import Field, SQLModel


class ColumnBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    position: int = 0
    is_terminal: bool = False


class ColumnDB(ColumnBase, table=True):
    __tablename__: ClassVar[str] = "column"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status_key: str = Field(min_length=1, max_length=50, unique=True)


class ColumnCreate(ColumnBase):
    status_key: str = Field(min_length=1, max_length=50)


class ColumnUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    position: int | None = None
    is_terminal: bool | None = None


class ColumnRead(ColumnBase):
    id: uuid.UUID
    status_key: str
