"""CLI entry point for ha_todo_manager."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Sequence

from ._version import __version__

logger = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ha_todo_manager",
        description="A Kanban-style todo manager for Home Assistant",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--host", default=None, help="Bind host (overrides HOST env var)")
    parser.add_argument("--port", type=int, default=None, help="Bind port (overrides PORT env var)")
    parser.add_argument(
        "--db-path", default=None, help="SQLite DB path (overrides DB_PATH env var)"
    )
    parser.add_argument("--log-level", default=None, help="Log level (overrides LOG_LEVEL env var)")
    parser.add_argument(
        "--webhook-secret",
        default=None,
        help="HA automation webhook secret (overrides WEBHOOK_SECRET env var)",
    )
    parser.add_argument(
        "--person-sync-interval-hours",
        # Not type=int: bashio::config can hand run.sh an empty string (e.g. when the
        # Supervisor API is unreachable, as in local/sandbox testing) instead of
        # falling back to its own default — int() would crash on "". Treated as
        # "not provided" below instead, same as the other optional string flags.
        default=None,
        help="HA person sync frequency (overrides PERSON_SYNC_INTERVAL_HOURS env var)",
    )
    parser.add_argument(
        "--materialise-interval-minutes",
        default=None,
        help="Recurrence materialisation frequency (overrides MATERIALISE_INTERVAL_MINUTES env var)",
    )

    args = parser.parse_args(argv)

    # Push CLI overrides into env before Settings is instantiated.
    if args.db_path:
        os.environ["DB_PATH"] = args.db_path
    if args.host:
        os.environ["HOST"] = args.host
    if args.port is not None:
        os.environ["PORT"] = str(args.port)
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    if args.webhook_secret:
        os.environ["WEBHOOK_SECRET"] = args.webhook_secret
    if args.person_sync_interval_hours:
        os.environ["PERSON_SYNC_INTERVAL_HOURS"] = args.person_sync_interval_hours
    if args.materialise_interval_minutes:
        os.environ["MATERIALISE_INTERVAL_MINUTES"] = args.materialise_interval_minutes

    from .settings import get_settings

    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    import uvicorn

    uvicorn.run(
        "ha_todo_manager.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
