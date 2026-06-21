# AGENTS.md – ha-todo (`ha_todo_manager`)

## Project Overview

`ha-todo` is a Home Assistant Ingress add-on providing a full-featured todo/task
management system with a Kanban view, assignees, recurring tasks, and bidirectional
Home Assistant automation integration. It is the spiritual successor to
`ha_shopping_list` and lives alongside it in this monorepo — see the root
[AGENTS.md](../AGENTS.md) for repository-wide conventions and the steps for adding
a new add-on.

The directory is named `ha_todo_manager` (matching the underscore `slug:` convention
used by `ha_shopping_list`), even though the project is referred to as "ha-todo" in
prose.

## Status

v1 design finalized (this document); implementation is being built incrementally.
The current code only contains the project skeleton (packaging, empty FastAPI app
with a health endpoint, empty `models/`/`routers`/`services/` packages) so that CI and
the Docker build are green from day one. Kanban data model, recurrence, HA person
sync, the webhook endpoint, and all frontend views are **not implemented yet** —
follow `spec/roadmap.md` for build order.

## Technology Stack

Identical to `ha_shopping_list` (see root [AGENTS.md](../AGENTS.md) for shared
tooling conventions):

- **Backend:** Python 3.13+, FastAPI (async), SQLModel (SQLAlchemy + Pydantic),
  SQLite (`/data/todo.db`), `python-dateutil` for RRULE recurrence.
- **Scheduler:** a single `asyncio` periodic task registered in the FastAPI `lifespan`
  context manager (no APScheduler) – ticks for recurrence materialisation and HA
  person sync.
- **Packaging:** `uv` + `hatchling` + `hatch-vcs` (`root = ".."`, same as
  `ha_shopping_list/pyproject.toml`).
- **Frontend:** React 19, Vite, Tailwind CSS, TanStack Query v5, React Router v6
  (hash-based, for Ingress compatibility), drag-and-drop via `@dnd-kit/core` +
  `@dnd-kit/sortable`.
- **Runtime:** HA Ingress only (no direct external port, unlike `ha_shopping_list`'s
  optional `8099/tcp`) – automation access goes through a dedicated webhook endpoint,
  not an open REST port.
- **Auth:** browser requests carry HA's `X-Ingress-User` header; webhook requests
  authenticate via a URL secret instead.

## Architecture

### Request flow

```
HA Automation  ──POST /api/webhook/ha/{secret}──▶
                                                   FastAPI Backend (ha_todo_manager)
Browser (HA Ingress) ─────────/api/* ────────────▶  │  SQLite (/data/todo.db)
                                                      │
                            /  (React SPA) ◀──────────┘
```

### Background scheduler

One `asyncio` periodic task, started in the FastAPI `lifespan`, runs once at startup
and then on two independent intervals (both configurable, see Configuration below):

- **Recurrence materialisation** (default every 60 min): finds recurring todos due for
  their next occurrence and creates the next instance.
- **HA person sync** (default every 6 h): refreshes the local `Person` table from HA's
  `person.*` entities via the Supervisor REST API.

The frontend also triggers a lightweight "materialise due tasks" call on initial API
load as a belt-and-suspenders measure, same idea as the original draft.

### HA person sync

On startup and on the periodic tick, the backend calls the Supervisor REST API
(`GET /core/api/states`, via `http://supervisor/core` + `SUPERVISOR_TOKEN` – both
treated as fixed runtime constants, not user-facing settings, since HA injects
`SUPERVISOR_TOKEN` automatically and the base URL never varies inside a real add-on
container) to fetch all `person.*` entities and upsert them into `Person`. The
`X-Ingress-User` HA user ID is mapped to a `Person` via `ha_user_id`, populated by
calling `/core/api/config/auth/current_user` during a given user's first request in a
session. This mapping drives the "my tasks" default filter.

## Data Model

### `Person`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `ha_user_id` | str unique nullable | HA internal user UUID |
| `ha_person_entity_id` | str unique nullable | e.g. `person.slarti` |
| `display_name` | str | |
| `avatar_url` | str nullable | pulled from HA state attributes |

### `Column`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `name` | str | |
| `position` | int | display order |
| `status_key` | str unique | canonical key: `backlog`, `todo`, `in_progress`, `done` |
| `is_terminal` | bool | tasks in terminal columns are "done" for recurrence purposes |

Seeded on first run with the four default columns. Additional columns can be created
by the user; `status_key` is free-form for custom columns.

### `Tag`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `name` | str unique | |
| `color` | str | hex |

### `Todo`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `title` | str | |
| `description` | str nullable | Markdown |
| `column_id` | UUID FK → Column | |
| `assignee_id` | UUID FK → Person nullable | |
| `due_date` | date nullable | |
| `priority` | int | 0 = none, 1 = low, 2 = medium, 3 = high |
| `position` | int | within-column sort order |
| `rrule` | str nullable | iCal RRULE string, e.g. `FREQ=WEEKLY;BYDAY=MO` |
| `next_due` | date nullable | next materialisation date for recurring tasks |
| `recurrence_parent_id` | UUID FK → Todo nullable | set on materialised instances |
| `source` | enum | `manual`, `ha_webhook` |
| `source_ref` | str nullable | arbitrary string from HA automation |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### `TodoTag` (association)
| Column | Type |
|---|---|
| `todo_id` | UUID FK |
| `tag_id` | UUID FK |

## API Design

All routes under `/api`. FastAPI auto-generates OpenAPI docs at `/api/docs`.

### Authentication / identity

Every browser request carries `X-Ingress-User`. A FastAPI dependency `get_current_user`
resolves or creates the `Person` record and attaches it to the request. Webhook
requests authenticate via the URL secret only.

### Todos

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/todos` | List todos. Query params: `column_id`, `assignee_id`, `mine` (bool), `tag_id`, `overdue` (bool) |
| `POST` | `/api/todos` | Create todo |
| `GET` | `/api/todos/{id}` | Get single todo |
| `PATCH` | `/api/todos/{id}` | Partial update (title, description, column, assignee, due_date, priority, rrule, position) |
| `DELETE` | `/api/todos/{id}` | Delete todo |
| `POST` | `/api/todos/{id}/complete` | Move to terminal column; materialise next recurrence if applicable |

### Columns

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/columns` | List all columns ordered by position |
| `POST` | `/api/columns` | Create column |
| `PATCH` | `/api/columns/{id}` | Rename, reorder, set `is_terminal` |
| `DELETE` | `/api/columns/{id}` | Delete (must not have todos) |

### Persons

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/persons` | List all known persons |
| `POST` | `/api/persons/sync` | Trigger manual HA person sync |

### Tags

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/tags` | List all tags |
| `POST` | `/api/tags` | Create tag |
| `DELETE` | `/api/tags/{id}` | Delete tag |

### Webhook (HA automations)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/webhook/ha/{secret}` | Create or complete a todo from an HA automation |

Webhook payload schema:

```json
{
  "action": "create" | "complete",
  "title": "string",
  "description": "string (optional)",
  "assignee_ha_person_entity_id": "person.xyz (optional)",
  "column_status_key": "todo (optional, default: todo)",
  "due_date": "YYYY-MM-DD (optional)",
  "priority": 0-3,
  "source_ref": "string (optional)",
  "todo_id": "uuid (required for action=complete)"
}
```

The secret is a generated-or-overridden add-on option (see Configuration); if unset
and no webhook secret could be generated, webhook endpoints return `501`.

### Recurrence

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/recurrence/materialise` | Manually trigger materialisation (also called on startup and by the scheduler) |

## Recurrence Logic

When a recurring todo (has `rrule` set) is completed:

1. The completed instance is moved to the terminal column and `updated_at` is stamped.
2. The scheduler (or `POST /api/recurrence/materialise`) computes `next_due` from the
   RRULE relative to today using `dateutil.rrule`.
3. A new `Todo` is created copying `title`, `description`, `assignee_id`, `column_id`
   (reset to the first non-terminal column), `priority`, `rrule`, `source`,
   `source_ref`, and `recurrence_parent_id` pointing at the root recurring todo.
4. `next_due` on the parent is advanced to the following occurrence.

The materialisation pass queries all todos where
`rrule IS NOT NULL AND next_due <= today AND recurrence_parent_id IS NULL` and applies
step 3. This logic lives in `services/recurrence.py` as pure functions (no DB access
in the RRULE math itself) so it's unit-testable without a database.

## Frontend Views

### Kanban board (default view)
- Columns rendered as swimlanes, horizontally scrollable on small screens.
- Cards are drag-and-drop between columns (update `column_id` + `position` on drop via
  `PATCH`).
- Card shows: title, assignee avatar, due date badge, priority indicator, tag chips,
  recurrence icon if `rrule` set.
- "My tasks" toggle in the header filters to `assignee_id = current_user`.

### List view
- Flat list, sortable by due date / priority / column.
- Same filter controls as Kanban.

### Card detail (slide-over panel)
- Full edit: title, description (Markdown editor), assignee picker, due date, priority,
  column, tags, RRULE builder.
- RRULE builder: simple UI covering daily / weekly (day picker) / monthly / yearly
  presets. Raw RRULE input as an advanced option.
- Source badge if created via webhook.

### Settings
- Column management (create, rename, reorder, mark terminal, delete).
- Tag management (create, colour-pick, delete).
- Person list (read-only, shows sync status).
- Webhook secret display (generated on first start, shown once, maskable thereafter).
  ⚠️ Token lifecycle / rotation strategy deferred to v2.

## Configuration

Exposed as HA add-on options in `config.yaml` (`options:`/`schema:`), rendered by the
Supervisor UI — **not** raw environment variables, to match the established
`ha_shopping_list` pattern (`log_level`, `api_key`). `run.sh` reads them via
`bashio::config` and passes them to the Python entrypoint as CLI flags, same as
`ha_shopping_list/run.sh`.

| Option | Default | Description |
|---|---|---|
| `log_level` | `info` | Verbosity: `trace`, `debug`, `info`, `warning`, `error`, `fatal` |
| `ha_webhook_secret` | `""` (auto-generate) | If left empty, a token is generated on first start, persisted in the DB, and shown once in the Settings UI. If set explicitly, overrides the generated token. |
| `person_sync_interval_hours` | `6` | HA person sync frequency |
| `materialise_interval_minutes` | `60` | Recurrence materialisation frequency |

`SUPERVISOR_TOKEN` and the Supervisor base URL (`http://supervisor/core`) are treated
as fixed runtime constants inside the app (see Architecture → HA person sync), not
add-on options — they're meaningless outside a real HA container and HA injects the
token automatically.

## Docker / Packaging

Same multi-stage structure as `ha_shopping_list/Dockerfile`:

- Build context is the **repo root**, not `ha_todo_manager/`, so that `.git/` stays
  reachable for `hatch-vcs` (see `[tool.hatch.version.raw-options] root = ".."` in
  `pyproject.toml` — this only resolves correctly if `.git/` and `ha_todo_manager/`
  keep the same relative layout inside the image as they have in a checkout).
- Stage 1: frontend build (Vite) on `node:22-alpine`, always `--platform=linux/amd64`
  since the output is pure JS.
- Stage 2: `uv sync --no-dev --frozen --no-editable` into a venv, with the built
  frontend `dist/` bundled into the package.
- Stage 3: HA base image (`build_from` per arch from `build.yaml`) with only the venv
  and `run.sh` copied in.
- `config.yaml` declares `ingress: true`, `ingress_port: 8100` (distinct from
  `ha_shopping_list`'s `8099` purely for clarity in logs/docs — no actual collision
  risk since each add-on runs in its own container).

## Coding Conventions

Inherits everything in the root [AGENTS.md](../AGENTS.md) (Python conventions, API
design rules, architecture rules, security checklist). Todo-specific module layout:

- `src/ha_todo_manager/models/` – one SQLModel module per entity (`person.py`,
  `column.py`, `tag.py`, `todo.py`, `todo_tag.py`).
- `src/ha_todo_manager/routers/` – one file per resource (`todos.py`, `columns.py`,
  `persons.py`, `tags.py`, `webhook.py`, `recurrence.py`); handlers call `services/`,
  never the ORM directly.
- `src/ha_todo_manager/services/` – business logic + all DB mutations.
- `src/ha_todo_manager/recurrence.py` – pure RRULE functions, no DB access, fully
  unit-testable.
- `src/ha_todo_manager/ha_client.py` – isolates all Supervisor REST calls (person
  sync, current-user lookup).
- `src/ha_todo_manager/scheduler.py` – the asyncio periodic task, registered from
  `app.py`'s lifespan.
- Frontend: one TanStack Query hook file per resource (`useTodos`, `useColumns`,
  `usePersons`, `useTags`). No business logic in components. Tailwind only – no CSS
  files except `index.css` for base/reset.

## Out of Scope (v1)

- Push notifications / HA persistent notifications on due tasks (v2).
- Sub-tasks / checklists within a card (v2).
- Attachments / file uploads.
- Multi-board support.
- Real-time sync between browser tabs (SSE / WebSocket).
