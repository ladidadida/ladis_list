"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from . import scheduler
from .database import create_db_and_tables, get_engine
from .routers import boards, columns, persons, recurrence, tags, todos, webhook
from .services import boards as boards_svc
from .services import webhook_secret
from .settings import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ingress-path injection middleware
# ---------------------------------------------------------------------------
# Same convention as ha_shopping_list/app.py: Home Assistant Ingress passes the
# add-on's sub-path via the X-Ingress-Path request header. The React SPA reads
# this value from <meta name="ingress-path">; we patch it into index.html.

_INGRESS_META_PLACEHOLDER = b'content=""'
_INGRESS_META_TEMPLATE = 'content="{path}"'


class _IngressPathMiddleware(BaseHTTPMiddleware):
    """Injects the X-Ingress-Path value into the index.html meta tag."""

    def __init__(self, app: ASGIApp, index_html: Path) -> None:
        super().__init__(app)
        self._index_html = index_html

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Only intercept the SPA fallback route's HTML — not /api/*, and not
        # FastAPI's own /docs, /redoc, /openapi.json (those are text/html too, and
        # without this check they'd get silently replaced with index.html).
        path = request.url.path
        if path.startswith(("/api", "/docs", "/redoc", "/openapi.json")):
            return response
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return response

        # Re-read and re-patch on every request rather than caching: index.html is a
        # few hundred bytes, so the I/O cost is negligible, and caching previously
        # caused stale content to be served for the lifetime of the process whenever
        # the build output changed underneath a running server (e.g. during local dev).
        ingress_path = request.headers.get("X-Ingress-Path", "").rstrip("/")
        raw = self._index_html.read_bytes()
        replacement = _INGRESS_META_TEMPLATE.format(path=ingress_path).encode()
        patched = raw.replace(_INGRESS_META_PLACEHOLDER, replacement, 1)

        return HTMLResponse(content=patched.decode(), status_code=response.status_code)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    create_db_and_tables()
    with Session(get_engine()) as session:
        boards_svc.ensure_default_board(session)
        webhook_secret.get_effective_secret(session)  # ensure it exists from first start

    settings = get_settings()
    tasks = [
        asyncio.create_task(scheduler.run_recurrence_loop(settings.materialise_interval_minutes)),
        asyncio.create_task(scheduler.run_person_sync_loop(settings.person_sync_interval_hours)),
    ]
    logger.info("ha-todo-manager started.")
    yield
    for task in tasks:
        task.cancel()
    for task in tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="ha-todo-manager",
        version="0.1.0",
        lifespan=_lifespan,
    )

    @app.get("/api/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(boards.router, prefix="/api")
    app.include_router(columns.router, prefix="/api")
    app.include_router(tags.router, prefix="/api")
    app.include_router(todos.router, prefix="/api")
    app.include_router(recurrence.router, prefix="/api")
    app.include_router(persons.router, prefix="/api")
    app.include_router(webhook.router, prefix="/api")

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
