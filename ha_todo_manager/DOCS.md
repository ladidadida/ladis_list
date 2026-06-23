# Todo Manager – Documentation

A Kanban-style todo manager for Home Assistant, with recurring tasks, assignees tied
to HA persons, multiple boards, and an automation webhook for creating/completing
todos from HA.

## Features

- Kanban board per board (Backlog / To Do / In Progress / Done by default),
  drag-and-drop between columns
- Multiple independent boards — each with its own columns and todos; tags and persons
  are shared across all of them (Settings → **Boards**)
- Assignees, tied to Home Assistant `person.*` entities (synced automatically) or
  created manually for household members without an HA account
- Recurring todos via RRULE (daily / weekly with weekday picker / monthly / yearly
  presets, or a raw RRULE string for anything else) — the next occurrence is created
  automatically once the current one is completed
- Tags with custom colours
- Due dates and priority (None / Low / Medium / High)
- "Nur meine Aufgaben" header filter — limits the board to todos assigned to the
  current HA user
- Automation webhook to create or complete todos from HA automations
- All data stored locally in `/data/todo.db` — survives restarts and backups

## Configuration

| Option | Default | Description |
|---|---|---|
| `log_level` | `info` | Logging verbosity: `trace`, `debug`, `info`, `warning`, `error`, `fatal` |
| `ha_webhook_secret` | `""` (auto-generate) | Secret for the automation webhook. Leave empty to have one generated on first start (shown once in Settings); set explicitly to use your own. |
| `person_sync_interval_hours` | `6` | How often persons are re-synced from HA's `person.*` entities |
| `materialise_interval_minutes` | `60` | How often due recurring todos are checked and their next occurrence created |

## Usage

The add-on appears in the Home Assistant sidebar as **Todo Manager** after
installation and start.

### Boards

New installs start with one board named **Board**. Open **⚙️ Einstellungen** →
**Boards** to rename it, add further boards (e.g. one per household area), or delete
one — deleting a board removes its columns and todos too, so you're asked to confirm
first. The board switcher (a dropdown in the header) only appears once there's more
than one board.

### Adding and editing todos

Click the **+** in a column's header to create a todo directly in that column, or the
**✏️** on an existing card to edit it. Both open the same detail panel: title,
description, column, priority, due date, assignee, tags, and recurrence.

### Moving todos

Drag a card to another column, or change its column from the detail panel.

### Recurrence

In the detail panel's **Wiederholung** section, pick Täglich / Wöchentlich /
Monatlich / Jährlich (weekly lets you pick specific weekdays), or "Eigene (RRULE)" to
enter a raw RRULE string (e.g. `FREQ=WEEKLY;BYDAY=MO,WE,FR`). When a recurring todo is
moved to a terminal column (e.g. "Done"), the next occurrence is created
automatically — either immediately or on the next periodic check
(`materialise_interval_minutes`).

### Assignees and persons

Open **⚙️ Einstellungen** → **Personen** to see everyone known to the add-on. Click
**Sync mit Home Assistant** to pull in current `person.*` entities, or add someone
manually (e.g. a household member without their own HA account) via the form at the
bottom. Assign a todo to someone from the detail panel's assignee dropdown.

### Tags

Manage tags (name + colour) under **⚙️ Einstellungen** → **Tags**. Assigned tags show
as coloured chips on a card; toggle them on/off per todo from the detail panel.

### "Nur meine Aufgaben"

The checkbox in the board header filters the visible todos to those assigned to you
(matched via your Home Assistant user). It's unchecked by default and stays as you
left it when switching boards, until you reload the page.

### Automations (webhook)

Each add-on instance has a webhook secret, shown once in **⚙️ Einstellungen** right
after first start — copy it then, since it isn't shown again. Automations can POST to:

```
POST /api/webhook/ha/<secret>
Content-Type: application/json

{
  "action": "create",
  "title": "Take out the trash",
  "description": "optional",
  "assignee_ha_person_entity_id": "person.slarti",
  "board_name": "optional, defaults to the first board",
  "column_status_key": "todo",
  "due_date": "2026-06-30",
  "priority": 2
}
```

To complete a todo instead, use `"action": "complete"` with `"todo_id": "<uuid>"`.
If you lose the secret, set `ha_webhook_secret` explicitly in the add-on's
Configuration tab and restart.

## Backup

The SQLite database at `/data/todo.db` is included in Home Assistant backups
automatically.
