"""RRULE-based recurrence: pure date math + materialisation orchestration.

The date math (first_due_date / advance_due_date) is pure and unit-tested without a
database. materialize_due_todos / _materialize_one touch the DB but stay thin
orchestration on top of that pure core.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from dateutil.rrule import rrulestr
from sqlmodel import Session, select

from ..models.column import ColumnDB
from ..models.todo import TodoDB
from ..models.todo_tag import TodoTagDB
from .columns import first_non_terminal_column


def _occurrence(rrule_str: str, dtstart: date, after: date, inclusive: bool) -> date | None:
    """Raises ValueError if `rrule_str` is not a parseable RRULE."""
    try:
        rule = rrulestr(rrule_str, dtstart=datetime.combine(dtstart, time.min))
    except Exception as exc:
        raise ValueError(f"Invalid RRULE {rrule_str!r}: {exc}") from exc
    occurrence = rule.after(datetime.combine(after, time.min), inc=inclusive)
    return occurrence.date() if occurrence else None


def first_due_date(rrule_str: str, dtstart: date) -> date | None:
    """First occurrence on/after `dtstart` (used when an rrule is first set)."""
    return _occurrence(rrule_str, dtstart, after=dtstart, inclusive=True)


def advance_due_date(rrule_str: str, dtstart: date, current_due: date) -> date | None:
    """Next occurrence strictly after `current_due`, anchored at the series' `dtstart`."""
    return _occurrence(rrule_str, dtstart, after=current_due, inclusive=False)


def _copy_tag_ids(session: Session, from_todo_id: uuid.UUID, to_todo_id: uuid.UUID) -> None:
    tag_ids = session.exec(select(TodoTagDB.tag_id).where(TodoTagDB.todo_id == from_todo_id)).all()
    for tag_id in tag_ids:
        session.add(TodoTagDB(todo_id=to_todo_id, tag_id=tag_id))


def materialize_one(session: Session, parent: TodoDB) -> TodoDB:
    """Create the next occurrence of `parent` and advance its `next_due`.

    `parent` must be a recurring root todo (`rrule` and `next_due` set).
    """
    if parent.rrule is None or parent.next_due is None:
        raise ValueError("parent must be a recurring todo with next_due set")

    parent_column = session.get(ColumnDB, parent.column_id)
    board_id = parent_column.board_id if parent_column else None
    # Stay within the same board as the parent — a global "first non-terminal
    # column" lookup would risk moving the new instance onto a different board.
    target_column = first_non_terminal_column(session, board_id) if board_id else None
    new_todo = TodoDB(
        title=parent.title,
        description=parent.description,
        column_id=target_column.id if target_column else parent.column_id,
        assignee_id=parent.assignee_id,
        priority=parent.priority,
        rrule=parent.rrule,
        source=parent.source,
        source_ref=parent.source_ref,
        recurrence_parent_id=parent.id,
    )
    session.add(new_todo)
    _copy_tag_ids(session, parent.id, new_todo.id)

    parent.next_due = advance_due_date(parent.rrule, parent.created_at.date(), parent.next_due)
    session.add(parent)
    session.commit()
    session.refresh(new_todo)
    return new_todo


def materialize_due_todos(session: Session) -> int:
    """Materialise the next occurrence for every recurring root todo that's due.

    Used by the periodic scheduler and the manual `/api/recurrence/materialise`
    endpoint — catches up on overdue recurrences, e.g. after a container restart.
    """
    today = date.today()
    due = session.exec(
        select(TodoDB).where(
            TodoDB.rrule.is_not(None),  # type: ignore[union-attr]
            TodoDB.recurrence_parent_id.is_(None),  # type: ignore[union-attr]
            TodoDB.next_due.is_not(None),  # type: ignore[union-attr]
            TodoDB.next_due <= today,  # type: ignore[operator]
        )
    ).all()
    for parent in due:
        materialize_one(session, parent)
    return len(due)
