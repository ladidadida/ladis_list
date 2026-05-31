"""Category DB table model and request/response schemas."""

from __future__ import annotations

from typing import ClassVar

from sqlmodel import Field, SQLModel


class CategoryBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    sort_order: int = 0


class CategoryDB(CategoryBase, table=True):
    __tablename__: ClassVar[str] = "category"

    id: int | None = Field(default=None, primary_key=True)


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int


class CategoryReorderItem(SQLModel):
    id: int
    sort_order: int
