"""API router for /api/persons."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from .. import ha_client
from ..database import get_session
from ..models.person import PersonRead
from ..services import persons as svc

router = APIRouter(prefix="/persons", tags=["persons"])


@router.get("", response_model=list[PersonRead])
def get_persons(session: Session = Depends(get_session)) -> list[PersonRead]:
    return svc.list_persons(session)  # type: ignore[return-value]


@router.post("/sync")
async def post_sync(session: Session = Depends(get_session)) -> dict[str, int]:
    try:
        entries = await ha_client.fetch_persons()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503, detail=f"Could not reach Home Assistant: {exc}"
        ) from exc
    count = svc.sync_persons(session, entries)
    return {"synced": count}
