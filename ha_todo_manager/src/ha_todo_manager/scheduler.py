"""Asyncio periodic tasks, registered from app.py's lifespan.

Two independent loops: recurrence materialisation and HA person sync. Each runs once
immediately at startup, then on its own interval.
"""

from __future__ import annotations

import asyncio
import logging

from sqlmodel import Session

from . import ha_client
from .database import get_engine
from .services import persons, recurrence

logger = logging.getLogger(__name__)


async def _materialise_tick() -> None:
    with Session(get_engine()) as session:
        count = recurrence.materialize_due_todos(session)
        if count:
            logger.info("Materialised %d recurring todo(s).", count)


async def run_recurrence_loop(interval_minutes: int) -> None:
    """Run a materialisation tick immediately, then every `interval_minutes`."""
    await _materialise_tick()
    while True:
        await asyncio.sleep(interval_minutes * 60)
        await _materialise_tick()


async def _person_sync_tick() -> None:
    try:
        entries = await ha_client.fetch_persons()
    except Exception:
        # Expected in local dev / sandboxes with no real Supervisor reachable at
        # http://supervisor/core — log and retry on the next tick rather than letting
        # the loop die after a single failure.
        logger.warning("HA person sync failed (Supervisor unreachable?)", exc_info=True)
        return
    with Session(get_engine()) as session:
        count = persons.sync_persons(session, entries)
    logger.info("Synced %d person(s) from Home Assistant.", count)


async def run_person_sync_loop(interval_hours: int) -> None:
    """Run a person-sync tick immediately, then every `interval_hours`."""
    await _person_sync_tick()
    while True:
        await asyncio.sleep(interval_hours * 3600)
        await _person_sync_tick()
