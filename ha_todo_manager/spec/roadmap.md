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

## Phase 3 – Home Assistant Integration ✅

- [x] `models/person.py`
- [x] `services/persons.py`, `routers/persons.py`
- [x] `ha_client.py` – Supervisor REST calls (`fetch_persons`, async `httpx`; state
      parsing split into a pure `parse_person_state` function, unit-tested)
- [x] `dependencies.py` (new — not in the original module list) — `get_current_user`
      resolving `X-Ingress-User` → `Person`
- [x] Person sync wired into the scheduler (`person_sync_interval_hours`), as its own
      loop alongside the existing recurrence loop (`scheduler.py` now has two:
      `run_recurrence_loop` / `run_person_sync_loop`)
- [x] `routers/webhook.py` – `POST /api/webhook/ha/{secret}` (create / complete
      actions), `GET /api/webhook/secret` (one-time reveal)
- [x] Webhook secret generation-on-first-start + persistence (`AppSecretDB`) +
      one-time display via the API
- [x] `ha_webhook_secret` config option override path
- [x] `Todo` model: `assignee_id`, `source`, `source_ref` (deferred since Phase 1);
      `GET /api/todos` gained `assignee_id`/`mine` filters

**Gap-fill decisions / deviations from the original design:**
- **No call to `/core/api/config/auth/current_user`.** `SUPERVISOR_TOKEN`
  authenticates as the Supervisor/add-on, not as the browsing human, so that endpoint
  can't resolve "who's asking" per-request. `X-Ingress-User` already carries the HA
  user id directly; `get_current_user` looks up/creates a `Person` from it (display
  name backfilled by the next person sync once a matching `person.*` entity with the
  same `user_id` is found).
- **Webhook "not configured" `501` no longer applies.** Since a secret is now always
  auto-generated and persisted on first access (`get_effective_secret`), there's no
  state where no secret exists — every webhook call validates against something.
- **New `503`** (`POST /api/persons/sync`, upstream Supervisor unreachable) added
  alongside the previously-documented `404`/`422`/`501` exceptions to the root
  AGENTS.md's strict status-code list — same category as the existing `501`
  carve-out (external-dependency-not-available), not a new pattern.
- **Person-sync scheduler tick swallows and logs exceptions** (`Supervisor
  unreachable?` warning) instead of propagating — otherwise the loop would die after
  one failure in any environment without a real Supervisor (which is every local/dev
  environment, including this monorepo's `bam serve`/`docker-serve`).
- **Found via real Docker container testing (not just `bam ci-checks`):**
  `person_sync_interval_hours`/`materialise_interval_minutes` were declared in
  `config.yaml` since Phase 0/2 but never actually wired through `run.sh`/`cli.py` —
  changing those add-on options in the HA UI had zero effect. Fixed by adding the
  matching CLI flags and `bashio::config` reads. While fixing it, found that
  `bashio::config` can hand back an empty string instead of falling back to its own
  default when the Supervisor API is unreachable (true for every sandbox/local-dev
  run) — `argparse`'s `type=int` crashed on `int("")`. Fixed by accepting these flags
  as plain strings and treating falsy values as "not provided", same as the other
  optional flags; `pydantic-settings` does the int coercion once a real value lands
  in the env var.
- **Frontend (assignee picker, persons list, webhook secret display UI) intentionally
  out of scope for this phase** — backend-only, per the original roadmap bullets.
  Confirmed with the user that `assignee_id: null` on browser-created todos is
  expected for now.

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
- [x] Kanban board (swimlanes, drag-and-drop via `@dnd-kit/core` + `@dnd-kit/sortable`),
      replacing the list view — `KanbanBoard` (single `DndContext`, horizontally
      scrollable swimlanes) → `KanbanColumn` (`useDroppable` + `SortableContext`) →
      `SortableTodoCard` (`useSortable` wrapper) → `TodoCard` (stays dnd-kit-agnostic,
      receives `dragHandleAttributes`/`dragHandleListeners` as props). Reordering
      updates only the todos whose `position` actually changed via a batched
      `useMoveTodo` hook (multiple `PATCH`s, one invalidate) — no new backend endpoint
      needed.
- [x] Card detail slide-over (`CardDetailPanel`) — full edit: title, description,
      column, due date, priority, tags, and an RRULE preset picker
      (`lib/rrule.ts`: täglich/wöchentlich-mit-Wochentagen/monatlich/jährlich/eigene
      RRULE), opened via a ✏️ button on the card. The card's inline column `<select>`
      was removed once this and drag-and-drop both covered moving a todo between
      columns — keeping all three was redundant (user feedback after testing).
- [ ] Settings page (column management, persons read-only, webhook secret display)
- [ ] React Router v6 (hash-based) once there's more than one view

**Found during manual check (list-view iteration):** creating a todo with `rrule`
failed with `sqlite3.OperationalError: table todo has no column named rrule` — not a
code bug, the local dev DB at `/tmp/ha-todo-manager-dev.db` predated the Phase 2 schema
changes (`SQLModel.metadata.create_all()` only creates missing tables, it doesn't alter
existing ones). Fixed by deleting the stale dev DB file. No migration tooling added —
not warranted pre-release with no real data to preserve.

**Found during manual check (Kanban iteration):** after rebuilding the frontend, the
browser still loaded old (now-deleted) JS/CSS asset hashes and showed a blank page. Not
a code bug — an earlier `bam serve` process from the previous iteration was never
actually killed (`pkill` had silently missed it), so it kept holding port 8100; a
second `bam serve` start failed to bind and exited, while the stale process kept
serving the old build. Fixed by `kill -9`-ing the stale PID (verified via `ss -tlnp`)
and starting a genuinely fresh process.

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
