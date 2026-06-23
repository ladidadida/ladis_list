"""API router for /api/webhook (HA automation integration)."""

from __future__ import annotations

import secrets
import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from ..database import get_session
from ..services import todos as todos_svc
from ..services import webhook_secret as secret_svc

router = APIRouter(prefix="/webhook", tags=["webhook"])


class WebhookPayload(BaseModel):
    action: Literal["create", "complete"]
    title: str | None = None
    description: str | None = None
    assignee_ha_person_entity_id: str | None = None
    # Omit to target the first board (by position) — fine for the common
    # single-board setup; only needed once more than one board exists.
    board_name: str | None = None
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

    result = todos_svc.create_from_webhook(
        session,
        title=payload.title,
        description=payload.description,
        board_name=payload.board_name,
        column_status_key=payload.column_status_key,
        assignee_ha_person_entity_id=payload.assignee_ha_person_entity_id,
        due_date=payload.due_date,
        priority=payload.priority,
        source_ref=payload.source_ref,
    )
    if result == "unknown_board":
        raise HTTPException(status_code=422, detail=f"Unknown board_name {payload.board_name!r}")
    if result == "unknown_column":
        raise HTTPException(
            status_code=422, detail=f"Unknown column_status_key {payload.column_status_key!r}"
        )
    return {"id": str(result.id)}
