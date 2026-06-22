"""Business logic for todo operations."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Literal

from sqlmodel import Session, select

from ..models.column import ColumnDB
from ..models.todo import TodoCreate, TodoDB, TodoSource, TodoUpdate
from ..models.todo_tag import TodoTagDB
from . import recurrence


def _utcnow() -> datetime:
    return datetime.now(UTC)


CompleteResult = Literal["not_found", "no_terminal_column"]


def get_tag_ids(session: Session, todo_id: uuid.UUID) -> list[uuid.UUID]:
    rows = session.exec(select(TodoTagDB.tag_id).where(TodoTagDB.todo_id == todo_id)).all()
    return list(rows)


def _set_tag_ids(session: Session, todo_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> None:
    existing = session.exec(select(TodoTagDB).where(TodoTagDB.todo_id == todo_id)).all()
    for link in existing:
        session.delete(link)
    for tag_id in tag_ids:
        session.add(TodoTagDB(todo_id=todo_id, tag_id=tag_id))


def list_todos(
    session: Session,
    column_id: uuid.UUID | None = None,
    tag_id: uuid.UUID | None = None,
    assignee_id: uuid.UUID | None = None,
    overdue: bool | None = None,
) -> list[TodoDB]:
    stmt = select(TodoDB)
    if column_id is not None:
        stmt = stmt.where(TodoDB.column_id == column_id)
    if assignee_id is not None:
        stmt = stmt.where(TodoDB.assignee_id == assignee_id)
    if tag_id is not None:
        stmt = stmt.join(TodoTagDB, TodoTagDB.todo_id == TodoDB.id).where(  # type: ignore[arg-type]
            TodoTagDB.tag_id == tag_id
        )
    if overdue:
        stmt = stmt.where(TodoDB.due_date.is_not(None), TodoDB.due_date < date.today())  # type: ignore[union-attr]
    return list(session.exec(stmt).all())


def create_todo(
    session: Session,
    data: TodoCreate,
    source: TodoSource = "manual",
    source_ref: str | None = None,
) -> TodoDB:
    todo = TodoDB.model_validate(data)
    todo.source = source
    todo.source_ref = source_ref
    if todo.rrule is not None:
        todo.next_due = recurrence.first_due_date(todo.rrule, date.today())
    session.add(todo)
    session.commit()
    _set_tag_ids(session, todo.id, data.tag_ids)
    session.commit()
    session.refresh(todo)
    return todo


def get_todo(session: Session, todo_id: uuid.UUID) -> TodoDB | None:
    return session.get(TodoDB, todo_id)


def update_todo(session: Session, todo_id: uuid.UUID, data: TodoUpdate) -> TodoDB | None:
    todo = session.get(TodoDB, todo_id)
    if todo is None:
        return None
    patch = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
    todo.sqlmodel_update(patch)
    if "rrule" in patch:
        todo.next_due = recurrence.first_due_date(todo.rrule, date.today()) if todo.rrule else None
    todo.updated_at = _utcnow()
    session.add(todo)
    if data.tag_ids is not None:
        _set_tag_ids(session, todo_id, data.tag_ids)
    session.commit()
    session.refresh(todo)
    return todo


def delete_todo(session: Session, todo_id: uuid.UUID) -> bool:
    todo = session.get(TodoDB, todo_id)
    if todo is None:
        return False
    session.delete(todo)
    session.commit()
    return True


def complete_todo(session: Session, todo_id: uuid.UUID) -> TodoDB | CompleteResult:
    todo = session.get(TodoDB, todo_id)
    if todo is None:
        return "not_found"
    terminal_column = session.exec(
        select(ColumnDB)
        .where(ColumnDB.is_terminal == True)  # noqa: E712
        .order_by(ColumnDB.position)  # type: ignore[arg-type]
    ).first()
    if terminal_column is None:
        return "no_terminal_column"
    todo.column_id = terminal_column.id
    todo.updated_at = _utcnow()
    session.add(todo)
    if todo.recurrence_parent_id is None and todo.rrule is not None:
        # Root recurring todo: spawn the next occurrence right away, regardless of
        # next_due (the periodic/manual sweep is what's date-gated, see recurrence.py).
        recurrence.materialize_one(session, todo)
    else:
        session.commit()
    session.refresh(todo)
    return todo
