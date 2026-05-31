"""Business logic for category operations."""

from __future__ import annotations

from sqlmodel import Session, select

from ..models.category import CategoryCreate, CategoryDB, CategoryReorderItem


def list_categories(session: Session) -> list[CategoryDB]:
    return list(session.exec(select(CategoryDB).order_by(CategoryDB.sort_order)).all())  # type: ignore[arg-type]


def create_category(session: Session, data: CategoryCreate) -> CategoryDB:
    category = CategoryDB.model_validate(data)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete_category(session: Session, category_id: int) -> bool:
    """Delete a category; items in that category become uncategorised."""
    category = session.get(CategoryDB, category_id)
    if category is None:
        return False
    session.delete(category)
    session.commit()
    return True


def reorder_categories(session: Session, items: list[CategoryReorderItem]) -> None:
    """Bulk-update sort_order for the given categories. Unknown IDs are silently ignored."""
    for item in items:
        category = session.get(CategoryDB, item.id)
        if category is not None:
            category.sort_order = item.sort_order
            session.add(category)
    session.commit()
