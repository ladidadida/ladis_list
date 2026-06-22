"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, Header
from sqlmodel import Session

from .database import get_session
from .models.person import PersonDB
from .services import persons as persons_svc


def get_current_user(
    session: Session = Depends(get_session),
    x_ingress_user: str | None = Header(default=None, alias="X-Ingress-User"),
) -> PersonDB | None:
    """Resolve the browsing HA user to a Person, creating a stub if not seen before.

    None when there's no X-Ingress-User header (e.g. local dev without real Ingress,
    or a request that didn't come through HA Ingress at all).
    """
    if not x_ingress_user:
        return None
    return persons_svc.get_or_create_by_ha_user_id(session, x_ingress_user)
