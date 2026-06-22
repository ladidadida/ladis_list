"""Business logic for person operations."""

from __future__ import annotations

import uuid

from sqlmodel import Session, select

from ..ha_client import PersonInfo
from ..models.person import PersonCreate, PersonDB
from ..models.todo import TodoDB


def list_persons(session: Session) -> list[PersonDB]:
    return list(session.exec(select(PersonDB).order_by(PersonDB.display_name)).all())  # type: ignore[arg-type]


def create_person(session: Session, data: PersonCreate) -> PersonDB:
    """Manually add a person without an HA account (ha_user_id/ha_person_entity_id unset)."""
    person = PersonDB.model_validate(data)
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


def delete_person(session: Session, person_id: uuid.UUID) -> bool:
    """Delete a person, unassigning (not blocking) any todos currently assigned to them."""
    person = session.get(PersonDB, person_id)
    if person is None:
        return False
    assigned = session.exec(select(TodoDB).where(TodoDB.assignee_id == person_id)).all()
    for todo in assigned:
        todo.assignee_id = None
        session.add(todo)
    session.delete(person)
    session.commit()
    return True


def get_or_create_by_ha_user_id(session: Session, ha_user_id: str) -> PersonDB:
    person = session.exec(select(PersonDB).where(PersonDB.ha_user_id == ha_user_id)).first()
    if person is not None:
        return person
    person = PersonDB(display_name=ha_user_id, ha_user_id=ha_user_id)
    session.add(person)
    session.commit()
    session.refresh(person)
    return person


def sync_persons(session: Session, entries: list[PersonInfo]) -> int:
    """Upsert Person rows from HA person.* state data. Returns the number synced."""
    for entry in entries:
        existing = session.exec(
            select(PersonDB).where(PersonDB.ha_person_entity_id == entry["ha_person_entity_id"])
        ).first()
        if existing is None and entry["ha_user_id"]:
            existing = session.exec(
                select(PersonDB).where(PersonDB.ha_user_id == entry["ha_user_id"])
            ).first()

        if existing is not None:
            existing.display_name = entry["display_name"]
            existing.ha_user_id = entry["ha_user_id"] or existing.ha_user_id
            existing.ha_person_entity_id = entry["ha_person_entity_id"]
            existing.avatar_url = entry["avatar_url"]
            session.add(existing)
        else:
            session.add(
                PersonDB(
                    display_name=entry["display_name"],
                    ha_user_id=entry["ha_user_id"],
                    ha_person_entity_id=entry["ha_person_entity_id"],
                    avatar_url=entry["avatar_url"],
                )
            )
    session.commit()
    return len(entries)
