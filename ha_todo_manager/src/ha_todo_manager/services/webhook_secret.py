"""Webhook secret lifecycle: generate-on-first-start, persist, one-time display.

An explicitly configured `ha_webhook_secret` add-on option always wins and is never
persisted to (or read from) the database. Otherwise a secret is generated once,
stored in `AppSecretDB`, and handed out via the API exactly once.
"""

from __future__ import annotations

import secrets

from sqlmodel import Session

from ..models.app_secret import AppSecretDB
from ..settings import get_settings

_WEBHOOK_SECRET_KEY = "webhook_secret"


def get_effective_secret(session: Session) -> str:
    """The secret to validate incoming webhook requests against."""
    configured = get_settings().webhook_secret
    if configured:
        return configured
    row = session.get(AppSecretDB, _WEBHOOK_SECRET_KEY)
    if row is None:
        row = AppSecretDB(key=_WEBHOOK_SECRET_KEY, value=secrets.token_urlsafe(24))
        session.add(row)
        session.commit()
    return row.value


def take_secret_to_display(session: Session) -> str | None:
    """Return the auto-generated secret exactly once.

    None if a secret was explicitly configured (nothing to reveal) or the
    auto-generated one was already shown before.
    """
    if get_settings().webhook_secret:
        return None
    get_effective_secret(session)  # ensure the row exists
    row = session.get(AppSecretDB, _WEBHOOK_SECRET_KEY)
    if row is None or row.displayed:
        return None
    row.displayed = True
    session.add(row)
    session.commit()
    return row.value
