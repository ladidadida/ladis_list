"""API router for /api/columns."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..database import get_session
from ..models.column import ColumnCreate, ColumnRead, ColumnUpdate
from ..services import columns as svc

router = APIRouter(prefix="/columns", tags=["columns"])


@router.get("", response_model=list[ColumnRead])
def get_columns(session: Session = Depends(get_session)) -> list[ColumnRead]:
    return svc.list_columns(session)  # type: ignore[return-value]


@router.post("", response_model=ColumnRead, status_code=201)
def post_column(data: ColumnCreate, session: Session = Depends(get_session)) -> ColumnRead:
    return svc.create_column(session, data)  # type: ignore[return-value]


@router.patch("/{column_id}", response_model=ColumnRead)
def patch_column(
    column_id: uuid.UUID,
    data: ColumnUpdate,
    session: Session = Depends(get_session),
) -> ColumnRead:
    column = svc.update_column(session, column_id, data)
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")
    return column  # type: ignore[return-value]


@router.delete("/{column_id}", status_code=204)
def delete_column(column_id: uuid.UUID, session: Session = Depends(get_session)) -> None:
    result = svc.delete_column(session, column_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Column not found")
    if result == "has_todos":
        raise HTTPException(status_code=422, detail="Column still has todos")
