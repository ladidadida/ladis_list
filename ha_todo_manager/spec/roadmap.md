# Roadmap – ha-todo-manager

Current date: 2026-06-21

---

## Status Legend

| Symbol | Meaning |
|---|---|
| ✅ | Done |
| 🔄 | In progress |
| ⬜ | Not started |

---

## Phase 0 – Project Bootstrap ✅

- [x] `pyproject.toml` with `uv` + `hatchling` + `hatch-vcs` (`root = ".."`)
- [x] `bam.yaml` task runner (lint, format, typecheck, test-unit, test-integration, test-component, build)
- [x] `ruff` + `pyright` configuration
- [x] CLI entry point (`ha_todo_manager.cli:main`)
- [x] Minimal FastAPI app (`/api/health`) + pytest scaffold (unit / integration / component)
- [x] Frontend skeleton (Vite + React 19 + Tailwind + TanStack Query) calling `/api/health`
- [x] `config.yaml`, `build.yaml`, `Dockerfile`, `run.sh`, `DOCS.md`, icon/logo placeholders
- [x] Registered in `.github/workflows/ci.yml`'s add-on matrix
- [x] `AGENTS.md`, `spec/roadmap.md`
- [ ] Real icon/logo artwork (current ones are generated placeholders)

**Exit criteria:** CI green, `docker build` succeeds, container serves `/api/health`. No
Kanban/recurrence/HA-integration/frontend-view code yet — that's Phases 1–4.

---

## Phase 1 – Backend MVP: Data Model, Services, CRUD ⬜

Goal: a fully functional REST API for todos/columns/tags, no recurrence or HA
integration yet.

- [ ] `models/column.py`, `models/tag.py`, `models/todo.py`, `models/todo_tag.py`
- [ ] `services/columns.py`, `services/tags.py`, `services/todos.py`
- [ ] `routers/columns.py`, `routers/tags.py`, `routers/todos.py` (without `/complete`
      recurrence wiring — plain column move)
- [ ] Seed the four default columns on first start
- [ ] Unit tests for services, integration tests for all routes

**Exit criteria:** Todos can be created, listed, filtered, updated, and deleted via the
API; columns and tags are manageable. No assignees, no recurrence, no webhook yet.

---

## Phase 2 – Recurrence ⬜

- [ ] `services/recurrence.py` – pure RRULE functions (no DB access), unit-tested
- [ ] `scheduler.py` – asyncio periodic task registered in `app.py`'s lifespan
- [ ] `routers/recurrence.py` – `POST /api/recurrence/materialise`
- [ ] `POST /api/todos/{id}/complete` wired to trigger materialisation when `rrule` is set
- [ ] `materialise_interval_minutes` config option actually wired into the scheduler

**Exit criteria:** Completing a recurring todo creates the next instance; a stale
container catches up on overdue recurrences on startup.

---

## Phase 3 – Home Assistant Integration ⬜

- [ ] `models/person.py`
- [ ] `services/persons.py`, `routers/persons.py`
- [ ] `ha_client.py` – Supervisor REST calls (list `person.*` states, current-user lookup)
- [ ] `get_current_user` FastAPI dependency resolving `X-Ingress-User` → `Person`
- [ ] Person sync wired into the scheduler (`person_sync_interval_hours`)
- [ ] `routers/webhook.py` – `POST /api/webhook/ha/{secret}` (create / complete actions)
- [ ] Webhook secret generation-on-first-start + persistence + one-time display
- [ ] `ha_webhook_secret` config option override path

**Exit criteria:** An HA automation can create and complete todos via the webhook; the
"my tasks" filter resolves the logged-in HA user to a `Person`.

---

## Phase 4 – Frontend Views ⬜

- [ ] `api/client.ts` (once there's a real API to wrap)
- [ ] Kanban board (swimlanes, drag-and-drop via `@dnd-kit/core` + `@dnd-kit/sortable`)
- [ ] List view
- [ ] Card detail slide-over (full edit + RRULE builder)
- [ ] Settings (columns, tags, persons read-only, webhook secret display)
- [ ] React Router v6 (hash-based) once there's more than one view

**Exit criteria:** All v1 user stories from `AGENTS.md` completable in the browser
without console errors on a mobile viewport.

---

## Phase 5 – HA Add-on Polish ⬜

- [ ] Real icon/logo artwork
- [ ] `DOCS.md` rewritten with actual installation/usage instructions
- [ ] Manual smoke-test on a real HA instance (amd64 + aarch64)
- [ ] `600` permissions on `/data/todo.db`, matching `ha_shopping_list`'s convention

---

## Known Constraints & Decisions

| Decision | Rationale |
|---|---|
| SQLite only (no Postgres) | Same reasoning as `ha_shopping_list`: HA add-ons run on embedded hardware, single-household scale. |
| No generic REST port, webhook-only automation access | Narrower attack surface than an open `/api/*` port; matches the original design's automation use case (create/complete actions) without needing full CRUD exposed externally. |
| `SUPERVISOR_TOKEN` / Supervisor base URL are fixed runtime constants, not add-on options | They're meaningless outside a real HA container and HA injects the token automatically — see `AGENTS.md` § Configuration. |
| Config via `config.yaml` options, not raw env vars | Matches the established HA add-on UX (`ha_shopping_list`'s `log_level`/`api_key` pattern) instead of the original draft's free-form env vars. |
