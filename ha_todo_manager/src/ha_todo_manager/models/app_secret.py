"""Small persistent key/value store for server-generated secrets.

Currently used only for the auto-generated webhook secret (see
services/webhook_secret.py) — generated once on first start, persisted so it survives
restarts, and revealed via the API exactly once (`displayed`).
"""

from __future__ import annotations

from typing import ClassVar

from sqlmodel import Field, SQLModel


class AppSecretDB(SQLModel, table=True):
    __tablename__: ClassVar[str] = "app_secret"

    key: str = Field(primary_key=True)
    value: str
    displayed: bool = False
