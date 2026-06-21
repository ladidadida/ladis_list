"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from .database import create_db_and_tables, get_engine
from .models.column import ColumnDB
from .routers import columns, tags, todos

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ingress-path injection middleware
# ---------------------------------------------------------------------------
# Same convention as ha_shopping_list/app.py: Home Assistant Ingress passes the
# add-on's sub-path via the X-Ingress-Path request header. The React SPA reads
# this value from <meta name="ingress-path">; we patch it into index.html.

_INGRESS_META_PLACEHOLDER = b'content=""'
_INGRESS_META_TEMPLATE = 'content="{path}"'

_DEFAULT_COLUMNS: list[tuple[str, str, bool]] = [
    ("Backlog", "backlog", False),
    ("To Do", "todo", False),
    ("In Progress", "in_progress", False),
    ("Done", "done", True),
]


class _IngressPathMiddleware(BaseHTTPMiddleware):
    """Injects the X-Ingress-Path value into the index.html meta tag."""

    def __init__(self, app: ASGIApp, index_html: Path) -> None:
        super().__init__(app)
        self._index_html = index_html
        # Cache: ingress_path -> patched HTML bytes
        self._cache: dict[str, bytes] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Only intercept HTML responses for index.html (SPA fallback routes)
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return response

        ingress_path = request.headers.get("X-Ingress-Path", "").rstrip("/")

        if ingress_path not in self._cache:
            raw = self._index_html.read_bytes()
            replacement = _INGRESS_META_TEMPLATE.format(path=ingress_path).encode()
            self._cache[ingress_path] = raw.replace(_INGRESS_META_PLACEHOLDER, replacement, 1)

        patched = self._cache[ingress_path]
        return HTMLResponse(content=patched.decode(), status_code=response.status_code)


def _seed_default_columns() -> None:
    with Session(get_engine()) as session:
        existing = session.exec(select(ColumnDB)).first()
        if existing is not None:
            return
        for position, (name, status_key, is_terminal) in enumerate(_DEFAULT_COLUMNS):
            session.add(
                ColumnDB(
                    name=name, status_key=status_key, position=position, is_terminal=is_terminal
                )
            )
        session.commit()
    logger.info("Seeded %d default columns.", len(_DEFAULT_COLUMNS))


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    create_db_and_tables()
    _seed_default_columns()
    logger.info("ha-todo-manager started.")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ha-todo-manager",
        version="0.1.0",
        lifespan=_lifespan,
    )

    @app.get("/api/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(columns.router, prefix="/api")
    app.include_router(tags.router, prefix="/api")
    app.include_router(todos.router, prefix="/api")

    # Serve the React SPA when the build artefact is present.
    # Non-editable installs (Docker): frontend is bundled inside the package.
    # Editable/dev installs: frontend is built at the project root.
    dist_dir = Path(__file__).parent / "frontend" / "dist"
    if not dist_dir.is_dir():
        dist_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
    index_html = dist_dir / "index.html"

    if dist_dir.is_dir() and index_html.is_file():
        # Serve static assets; mount under /assets to avoid colliding with /.
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa_fallback(full_path: str, request: Request) -> FileResponse:
            return FileResponse(str(index_html))

        # Inject the HA Ingress path into every index.html response.
        app.add_middleware(_IngressPathMiddleware, index_html=index_html)
    else:
        # Frontend not built yet – return a helpful placeholder.
        @app.get("/", include_in_schema=False)
        async def root(request: Request) -> HTMLResponse:
            return HTMLResponse(
                "<html><body><h1>ha-todo-manager</h1>"
                "<p>Backend is running. Frontend not built yet.</p>"
                "<p>API docs: <a href='/docs'>/docs</a></p></body></html>"
            )

    return app
