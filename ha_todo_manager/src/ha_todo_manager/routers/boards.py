"""API router for /api/boards."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..database import get_session
from ..models.board import BoardCreate, BoardRead, BoardUpdate
from ..services import boards as svc

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("", response_model=list[BoardRead])
def get_boards(session: Session = Depends(get_session)) -> list[BoardRead]:
    return svc.list_boards(session)  # type: ignore[return-value]


@router.post("", response_model=BoardRead, status_code=201)
def post_board(data: BoardCreate, session: Session = Depends(get_session)) -> BoardRead:
    return svc.create_board(session, data)  # type: ignore[return-value]


@router.patch("/{board_id}", response_model=BoardRead)
def patch_board(
    board_id: uuid.UUID,
    data: BoardUpdate,
    session: Session = Depends(get_session),
) -> BoardRead:
    board = svc.update_board(session, board_id, data)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return board  # type: ignore[return-value]


@router.delete("/{board_id}", status_code=204)
def delete_board(board_id: uuid.UUID, session: Session = Depends(get_session)) -> None:
    result = svc.delete_board(session, board_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Board not found")
    if result == "last_board":
        raise HTTPException(status_code=422, detail="Cannot delete the only remaining board")
