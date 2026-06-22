"""API router for /api/webhook (HA automation integration)."""

from __future__ import annotations

import secrets
import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..database import get_session
from ..models.column import ColumnDB
from ..models.person import PersonDB
from ..models.todo import TodoCreate
from ..services import todos as todos_svc
from ..services import webhook_secret as secret_svc

router = APIRouter(prefix="/webhook", tags=["webhook"])


class WebhookPayload(BaseModel):
    action: Literal["create", "complete"]
    title: str | None = None
    description: str | None = None
    assignee_ha_person_entity_id: str | None = None
    column_status_key: str = "todo"
    due_date: date | None = None
    priority: int = 0
    source_ref: str | None = None
    todo_id: uuid.UUID | None = None


@router.get("/secret")
def get_webhook_secret(session: Session = Depends(get_session)) -> dict[str, str]:
    secret = secret_svc.take_secret_to_display(session)
    if secret is None:
        raise HTTPException(status_code=404, detail="No secret to display")
    return {"secret": secret}


@router.post("/ha/{provided_secret}")
def post_webhook(
    provided_secret: str,
    payload: WebhookPayload,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    expected = secret_svc.get_effective_secret(session)
    if not secrets.compare_digest(provided_secret, expected):
        raise HTTPException(status_code=404, detail="Not found")

    if payload.action == "complete":
        if payload.todo_id is None:
            raise HTTPException(status_code=422, detail="todo_id is required for action=complete")
        result = todos_svc.complete_todo(session, payload.todo_id)
        if result == "not_found":
            raise HTTPException(status_code=404, detail="Todo not found")
        if result == "no_terminal_column":
            raise HTTPException(status_code=422, detail="No terminal column configured")
        return {"id": str(result.id)}

    # action == "create"
    if not payload.title:
        raise HTTPException(status_code=422, detail="title is required for action=create")
    column = session.exec(
        select(ColumnDB).where(ColumnDB.status_key == payload.column_status_key)
    ).first()
    if column is None:
        raise HTTPException(
            status_code=422, detail=f"Unknown column_status_key {payload.column_status_key!r}"
        )
    assignee_id = None
    if payload.assignee_ha_person_entity_id:
        person = session.exec(
            select(PersonDB).where(
                PersonDB.ha_person_entity_id == payload.assignee_ha_person_entity_id
            )
        ).first()
        assignee_id = person.id if person else None

    data = TodoCreate(
        title=payload.title,
        description=payload.description,
        column_id=column.id,
        assignee_id=assignee_id,
        due_date=payload.due_date,
        priority=payload.priority,
    )
    todo = todos_svc.create_todo(session, data, source="ha_webhook", source_ref=payload.source_ref)
    return {"id": str(todo.id)}
