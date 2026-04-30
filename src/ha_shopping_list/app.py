"""FastAPI application factory."""

from __future__ import annotations

import logging
import os
import stat
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlmodel import Session, select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from .database import create_db_and_tables, get_engine
from .models.category import CategoryDB
from .models.shopping_list import ShoppingListDB
from .routers import categories, items, shopping_lists
from .settings import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ingress-path injection middleware
# ---------------------------------------------------------------------------
# Home Assistant Ingress passes the add-on's sub-path via the
# X-Ingress-Path request header (e.g. "/api/hassio_ingress/xxxx").
# The React SPA reads this value from <meta name="ingress-path">.
# We intercept index.html responses and patch the meta tag so the
# frontend API client can prepend the correct base path to every request.

_INGRESS_META_PLACEHOLDER = b'content=""'
_INGRESS_META_TEMPLATE = 'content="{path}"'


class _APIKeyMiddleware(BaseHTTPMiddleware):
    """Protects /api/v1/ routes when an api_key is configured.

    Rules:
    - If no api_key is configured: all requests pass through (existing behaviour,
      security provided by HA Ingress).
    - If an api_key is configured:
        - Requests arriving via HA Ingress carry an ``X-Ingress-Path`` header
          added by the HA nginx proxy → allowed unconditionally.
        - All other requests must supply ``X-API-Key: <key>`` → 401 otherwise.
    - Non-API paths (static assets, SPA) are never blocked.
    """

    def __init__(self, app: ASGIApp, api_key: str) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._api_key and request.url.path.startswith("/api/"):
            # Ingress requests are identified by the X-Ingress-Path header that
            # HA's nginx proxy injects – no key needed for those.
            if not request.headers.get("X-Ingress-Path"):
                supplied = request.headers.get("X-API-Key", "")
                if supplied != self._api_key:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Missing or invalid API key"},
                    )
        return await call_next(request)


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


_DEFAULT_CATEGORIES: list[tuple[str, int]] = [
    ("Obst & Gemüse", 0),
    ("Fleisch & Fisch", 1),
    ("Milchprodukte", 2),
    ("Tiefkühl", 3),
    ("Backwaren", 4),
    ("Getränke", 5),
    ("Haushalt", 6),
    ("Sonstiges", 7),
]


def _migrate_db() -> None:
    """Add columns that were introduced after the initial schema."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(item)"))
        existing_cols = {row[1] for row in result}
        if "list_id" not in existing_cols:
            conn.execute(text("ALTER TABLE item ADD COLUMN list_id INTEGER"))
            conn.commit()
            logger.info("Migrated: added list_id column to item table.")


def _seed_default_list() -> int:
    """Ensure a default shopping list exists; returns its id."""
    with Session(get_engine()) as session:
        existing = session.exec(select(ShoppingListDB)).first()
        if existing is not None:
            return existing.id  # type: ignore[return-value]
        default_list = ShoppingListDB(name="Einkaufsliste", sort_order=0)
        session.add(default_list)
        session.commit()
        session.refresh(default_list)
        logger.info("Seeded default shopping list (id=%d).", default_list.id)
        return default_list.id  # type: ignore[return-value]


def _assign_orphan_items(default_list_id: int) -> None:
    """Assign items with no list to the default list (one-time migration)."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE item SET list_id = :lid WHERE list_id IS NULL"),
            {"lid": default_list_id},
        )
        conn.commit()


def _seed_categories() -> None:
    with Session(get_engine()) as session:
        existing = session.exec(select(CategoryDB)).first()
        if existing is not None:
            return
        for name, order in _DEFAULT_CATEGORIES:
            session.add(CategoryDB(name=name, sort_order=order))
        session.commit()
    logger.info("Seeded %d default categories.", len(_DEFAULT_CATEGORIES))


def _ensure_db_permissions() -> None:
    db_path = str(get_settings().db_path)
    if os.path.exists(db_path):
        os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    create_db_and_tables()
    _migrate_db()
    _ensure_db_permissions()
    default_list_id = _seed_default_list()
    _assign_orphan_items(default_list_id)
    _seed_categories()
    logger.info("ha-shopping-list started.")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ha-shopping-list",
        version="1.0.0",
        lifespan=_lifespan,
    )

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(categories.router, prefix="/api/v1")
    app.include_router(items.router, prefix="/api/v1")
    app.include_router(shopping_lists.router, prefix="/api/v1")

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
                "<html><body><h1>ha-shopping-list</h1>"
                "<p>Backend is running. Frontend not built yet.</p>"
                "<p>API docs: <a href='/docs'>/docs</a></p></body></html>"
            )

    api_key = get_settings().api_key
    if api_key:
        app.add_middleware(_APIKeyMiddleware, api_key=api_key)

    return app
