"""Business logic for board operations."""

from __future__ import annotations

import logging
import uuid
from typing import Literal

from sqlmodel import Session, select

from ..models.board import BoardCreate, BoardDB, BoardUpdate
from ..models.column import ColumnDB
from ..models.todo import TodoDB
from ..models.todo_tag import TodoTagDB

logger = logging.getLogger(__name__)

DeleteResult = Literal["deleted", "not_found", "last_board"]

DEFAULT_COLUMNS: list[tuple[str, str, bool]] = [
    ("Backlog", "backlog", False),
    ("To Do", "todo", False),
    ("In Progress", "in_progress", False),
    ("Done", "done", True),
]


def list_boards(session: Session) -> list[BoardDB]:
    return list(session.exec(select(BoardDB).order_by(BoardDB.position)).all())  # type: ignore[arg-type]


def _seed_default_columns(session: Session, board_id: uuid.UUID) -> None:
    for position, (name, status_key, is_terminal) in enumerate(DEFAULT_COLUMNS):
        session.add(
            ColumnDB(
                board_id=board_id,
                name=name,
                status_key=status_key,
                position=position,
                is_terminal=is_terminal,
            )
        )


def create_board(session: Session, data: BoardCreate) -> BoardDB:
    """New boards get the same default columns as the very first one, so they're
    immediately usable."""
    board = BoardDB.model_validate(data)
    session.add(board)
    session.commit()
    session.refresh(board)
    _seed_default_columns(session, board.id)
    session.commit()
    return board


def update_board(session: Session, board_id: uuid.UUID, data: BoardUpdate) -> BoardDB | None:
    board = session.get(BoardDB, board_id)
    if board is None:
        return None
    patch = data.model_dump(exclude_unset=True)
    board.sqlmodel_update(patch)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


def delete_board(session: Session, board_id: uuid.UUID) -> DeleteResult:
    """Cascades: deletes the board's columns and their todos (and tag links). The
    only remaining board can't be deleted — there must always be at least one."""
    board = session.get(BoardDB, board_id)
    if board is None:
        return "not_found"
    if len(session.exec(select(BoardDB.id)).all()) <= 1:
        return "last_board"

    columns = session.exec(select(ColumnDB).where(ColumnDB.board_id == board_id)).all()
    column_ids = [c.id for c in columns]
    if column_ids:
        todos = session.exec(select(TodoDB).where(TodoDB.column_id.in_(column_ids))).all()  # type: ignore[attr-defined]
        todo_ids = [t.id for t in todos]
        if todo_ids:
            links = session.exec(
                select(TodoTagDB).where(TodoTagDB.todo_id.in_(todo_ids))  # type: ignore[attr-defined]
            ).all()
            for link in links:
                session.delete(link)
            for todo in todos:
                session.delete(todo)
        for column in columns:
            session.delete(column)
    session.delete(board)
    session.commit()
    return "deleted"


def ensure_default_board(session: Session) -> BoardDB:
    """Called once at startup: create the first board (with default columns) if none
    exists yet."""
    existing = session.exec(select(BoardDB)).first()
    if existing is not None:
        return existing
    board = BoardDB(name="Board", position=0)
    session.add(board)
    session.commit()
    session.refresh(board)
    _seed_default_columns(session, board.id)
    session.commit()
    logger.info("Seeded default board %r with %d columns.", board.name, len(DEFAULT_COLUMNS))
    return board
