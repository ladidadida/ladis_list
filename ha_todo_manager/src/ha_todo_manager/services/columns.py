"""Business logic for column operations."""

from __future__ import annotations

import uuid
from typing import Literal

from sqlmodel import Session, select

from ..models.column import ColumnCreate, ColumnDB, ColumnUpdate
from ..models.todo import TodoDB

DeleteResult = Literal["deleted", "not_found", "has_todos"]


def list_columns(session: Session) -> list[ColumnDB]:
    return list(session.exec(select(ColumnDB).order_by(ColumnDB.position)).all())  # type: ignore[arg-type]


def create_column(session: Session, data: ColumnCreate) -> ColumnDB:
    column = ColumnDB.model_validate(data)
    session.add(column)
    session.commit()
    session.refresh(column)
    return column


def update_column(session: Session, column_id: uuid.UUID, data: ColumnUpdate) -> ColumnDB | None:
    column = session.get(ColumnDB, column_id)
    if column is None:
        return None
    patch = data.model_dump(exclude_unset=True)
    column.sqlmodel_update(patch)
    session.add(column)
    session.commit()
    session.refresh(column)
    return column


def delete_column(session: Session, column_id: uuid.UUID) -> DeleteResult:
    column = session.get(ColumnDB, column_id)
    if column is None:
        return "not_found"
    has_todos = session.exec(select(TodoDB).where(TodoDB.column_id == column_id).limit(1)).first()
    if has_todos is not None:
        return "has_todos"
    session.delete(column)
    session.commit()
    return "deleted"
