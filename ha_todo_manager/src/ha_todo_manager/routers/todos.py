"""API router for /api/todos."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ..database import get_session
from ..dependencies import get_current_user
from ..models.person import PersonDB
from ..models.todo import TodoCreate, TodoDB, TodoRead, TodoUpdate
from ..services import todos as svc

router = APIRouter(prefix="/todos", tags=["todos"])


def _to_read(session: Session, todo: TodoDB) -> TodoRead:
    return TodoRead(**todo.model_dump(), tag_ids=svc.get_tag_ids(session, todo.id))


@router.get("", response_model=list[TodoRead])
def get_todos(
    column_id: uuid.UUID | None = Query(default=None),
    tag_id: uuid.UUID | None = Query(default=None),
    assignee_id: uuid.UUID | None = Query(default=None),
    board_id: uuid.UUID | None = Query(default=None),
    overdue: bool | None = Query(default=None),
    mine: bool = Query(default=False),
    current_user: PersonDB | None = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[TodoRead]:
    if mine:
        if current_user is None:
            return []
        assignee_id = current_user.id
    todos = svc.list_todos(
        session,
        column_id=column_id,
        tag_id=tag_id,
        assignee_id=assignee_id,
        board_id=board_id,
        overdue=overdue,
    )
    return [_to_read(session, todo) for todo in todos]


@router.post("", response_model=TodoRead, status_code=201)
def post_todo(data: TodoCreate, session: Session = Depends(get_session)) -> TodoRead:
    try:
        todo = svc.create_todo(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_read(session, todo)


@router.get("/{todo_id}", response_model=TodoRead)
def get_todo(todo_id: uuid.UUID, session: Session = Depends(get_session)) -> TodoRead:
    todo = svc.get_todo(session, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return _to_read(session, todo)


@router.patch("/{todo_id}", response_model=TodoRead)
def patch_todo(
    todo_id: uuid.UUID,
    data: TodoUpdate,
    session: Session = Depends(get_session),
) -> TodoRead:
    try:
        todo = svc.update_todo(session, todo_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return _to_read(session, todo)


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: uuid.UUID, session: Session = Depends(get_session)) -> None:
    if not svc.delete_todo(session, todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")


@router.post("/{todo_id}/complete", response_model=TodoRead)
def complete_todo(todo_id: uuid.UUID, session: Session = Depends(get_session)) -> TodoRead:
    result = svc.complete_todo(session, todo_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Todo not found")
    if result == "no_terminal_column":
        raise HTTPException(status_code=422, detail="No terminal column configured")
    return _to_read(session, result)
