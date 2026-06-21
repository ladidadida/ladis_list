"""API router for /api/tags."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..database import get_session
from ..models.tag import TagCreate, TagRead
from ..services import tags as svc

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
def get_tags(session: Session = Depends(get_session)) -> list[TagRead]:
    return svc.list_tags(session)  # type: ignore[return-value]


@router.post("", response_model=TagRead, status_code=201)
def post_tag(data: TagCreate, session: Session = Depends(get_session)) -> TagRead:
    return svc.create_tag(session, data)  # type: ignore[return-value]


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: uuid.UUID, session: Session = Depends(get_session)) -> None:
    if not svc.delete_tag(session, tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
