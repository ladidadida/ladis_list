"""API router for /api/v1/categories."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..database import get_session
from ..models.category import CategoryCreate, CategoryRead, CategoryReorderItem
from ..services import categories as svc

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def get_categories(session: Session = Depends(get_session)) -> list[CategoryRead]:
    return svc.list_categories(session)  # type: ignore[return-value]


@router.post("", response_model=CategoryRead, status_code=201)
def post_category(data: CategoryCreate, session: Session = Depends(get_session)) -> CategoryRead:
    return svc.create_category(session, data)  # type: ignore[return-value]


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, session: Session = Depends(get_session)) -> None:
    if not svc.delete_category(session, category_id):
        raise HTTPException(status_code=404, detail="Category not found")


@router.patch("/reorder", status_code=204)
def patch_reorder(
    data: list[CategoryReorderItem],
    session: Session = Depends(get_session),
) -> None:
    svc.reorder_categories(session, data)
