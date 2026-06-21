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
- [x] Frontend SPA serving wired into `app.py` (static mount + SPA fallback + HA
      ingress-path injection middleware, mirroring `ha_shopping_list/app.py`; no
      `api_key` middleware since this add-on has no direct REST port). This was
      missing from the initial skeleton — `bam serve`/`docker-serve` served only
      `/api/health`, nothing at `/`.
- [ ] Real icon/logo artwork (current ones are generated placeholders)

**Exit criteria:** CI green, `docker build` succeeds, container serves `/api/health`. No
Kanban/recurrence/HA-integration/frontend-view code yet — that's Phases 1–4.

---

## Phase 1 – Backend MVP: Data Model, Services, CRUD ✅

Goal: a fully functional REST API for todos/columns/tags, no recurrence or HA
integration yet.

- [x] `models/column.py`, `models/tag.py`, `models/todo.py`, `models/todo_tag.py`
- [x] `services/columns.py`, `services/tags.py`, `services/todos.py`
- [x] `routers/columns.py`, `routers/tags.py`, `routers/todos.py` (without `/complete`
      recurrence wiring — plain column move)
- [x] Seed the four default columns on first start
- [x] Integration tests for all routes (no separate mocked-session unit tests — same
      convention as `ha_shopping_list`, which covers services via API-level integration
      tests instead)

**Note:** tag association on a todo is exposed as `tag_ids` on create/update/read,
filling a gap the original API design table didn't spell out explicitly (it only
listed `tag_id` as a list filter, but `models/todo_tag.py` was in scope for this phase
and needs a way to be exercised through the API).

**Exit criteria:** Todos can be created, listed, filtered, updated, and deleted via the
API; columns and tags are manageable. No assignees, no recurrence, no webhook yet.

---

## Phase 2 – Recurrence ✅

- [x] `services/recurrence.py` – pure RRULE functions (no DB access), unit-tested
- [x] `scheduler.py` – asyncio periodic task registered in `app.py`'s lifespan
- [x] `routers/recurrence.py` – `POST /api/recurrence/materialise`
- [x] `POST /api/todos/{id}/complete` wired to trigger materialisation when `rrule` is set
- [x] `materialise_interval_minutes` config option actually wired into the scheduler

**Gap-fill decisions** (design didn't spell these out, same pattern as Phase 1's
`tag_ids` note):
- RRULE `dtstart` anchor = the root todo's `created_at.date()` (no separate "series
  start date" field exists).
- `/complete`-triggered materialisation is **not** date-gated (always spawns the next
  occurrence); the periodic/manual sweep **is** gated by `next_due <= today` (that's
  the "stale container catches up" case).
- Assignee/source/source_ref are not copied when materialising — they don't exist yet
  (Phase 3). Tags are copied.
- `POST /api/recurrence/materialise` returns `{"materialised": <count>}`.
- Invalid RRULE strings → `422`.

**Bug found during manual check and fixed in the same iteration:** `_IngressPathMiddleware`
(added for the Phase 0 SPA-serving fix) intercepted *any* `text/html` response and
replaced it with `index.html` — including FastAPI's own `/docs` and `/redoc`. Fixed by
excluding `/api`, `/docs`, `/redoc`, `/openapi.json` from the middleware. Regression
test added in `tests/integration/test_root.py`. Worth checking whether
`ha_shopping_list/app.py` has the same latent bug (same code, copied 1:1) — not fixed
here, out of scope for this iteration.

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

## Phase 4 – Frontend Views 🔄

Started ahead of Phase 3 (HA Integration) on request, to get a real frontend usable
for manual testing of columns/tags/todos/recurrence sooner.

- [x] `api/client.ts` – typed fetch wrappers for columns/tags/todos
- [x] One TanStack Query hook file per resource (`useColumns`, `useTags`, `useTodos`)
- [x] Simple list view (`ColumnSection` + `TodoCard`) — columns as plain sections, no
      drag-and-drop yet; moving a todo between columns is a `<select>` on the card
- [x] `AddTodoForm` (title, column, due date, priority, plain-text `rrule` field, tag
      multi-select)
- [x] `TagManager` — minimal inline create/delete, standing in for the full Settings
      page for now
- [ ] Kanban board (swimlanes, drag-and-drop via `@dnd-kit/core` + `@dnd-kit/sortable`)
      — deferred; the `<select>`-based column move is the stand-in
- [ ] Card detail slide-over (full edit + RRULE builder with presets — currently a
      plain text input)
- [ ] Settings page (column management, persons read-only, webhook secret display)
- [ ] React Router v6 (hash-based) once there's more than one view

**Found during manual check:** creating a todo with `rrule` failed with
`sqlite3.OperationalError: table todo has no column named rrule` — not a code bug, the
local dev DB at `/tmp/ha-todo-manager-dev.db` predated the Phase 2 schema changes
(`SQLModel.metadata.create_all()` only creates missing tables, it doesn't alter
existing ones). Fixed by deleting the stale dev DB file. No migration tooling added —
not warranted pre-release with no real data to preserve.

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
