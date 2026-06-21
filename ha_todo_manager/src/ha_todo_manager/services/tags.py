"""Business logic for tag operations."""

from __future__ import annotations

import uuid

from sqlmodel import Session, select

from ..models.tag import TagCreate, TagDB


def list_tags(session: Session) -> list[TagDB]:
    return list(session.exec(select(TagDB).order_by(TagDB.name)).all())


def create_tag(session: Session, data: TagCreate) -> TagDB:
    tag = TagDB.model_validate(data)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


def delete_tag(session: Session, tag_id: uuid.UUID) -> bool:
    tag = session.get(TagDB, tag_id)
    if tag is None:
        return False
    session.delete(tag)
    session.commit()
    return True
