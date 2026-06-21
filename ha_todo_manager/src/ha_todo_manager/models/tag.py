"""Tag DB table model and request/response schemas."""

from __future__ import annotations

import uuid
from typing import ClassVar

from sqlmodel import Field, SQLModel


class TagBase(SQLModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(min_length=1, max_length=20)


class TagDB(TagBase, table=True):
    __tablename__: ClassVar[str] = "tag"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(min_length=1, max_length=50, unique=True)


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    id: uuid.UUID
