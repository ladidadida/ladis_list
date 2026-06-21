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
