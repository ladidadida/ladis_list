# Shopping List – Documentation

A fast, mobile-friendly shopping list add-on for Home Assistant.

## Features

- Multiple named lists (e.g. one per store)
- Items organised by category within each list
- Drag-to-reorder categories
- Inline item editing (name, quantity, category)
- Quick-add row directly below each category
- Individual item delete, or bulk-delete all checked (done) items per list
- A direct REST API (port `8099`), separate from the Ingress UI, for Home Assistant
  automations
- All data stored locally in `/data/shoppinglist.db` – survives restarts and backups

## Configuration

| Option | Default | Description |
|---|---|---|
| `log_level` | `info` | Logging verbosity: `trace`, `debug`, `info`, `warning`, `error`, `fatal` |
| `api_key` | `""` (disabled) | If set, requests to the REST API (port `8099`) that don't come through HA Ingress must send a matching `X-API-Key` header. Leave empty to allow any request on that port. |

## Usage

The add-on appears in the Home Assistant sidebar as **Shopping List** after installation and start.
All household members (not just admins) can access it.

### Lists

Click the **🛒 list name** in the top-left of the header to open the list drawer where you can create or delete lists.
The default list is created automatically on first start.

### Categories

Click **🏷️ Kategorien** in the header (top right) to open the category manager.
Categories are shared across all lists. Create or delete them here, and drag the
**⠿** handle to reorder them — the order applies everywhere categories are shown.

### Adding items

- Use the form at the top to add an item to any category.
- Click **+** next to a category heading to add directly into that category without touching the top form.

### Editing and deleting items

Hover over any item and click the **✏️** button that appears to open an inline edit
form (name, quantity, category), or **✕** to delete it directly. Press **Speichern**
to save or **Abbrechen** (or Escape) to cancel the edit form; it also has its own
**Löschen** button.

On a touchscreen, tap an item to check it off; press and hold (~0.5s) to open the edit
form instead, since there's no hover state to reveal the ✏️/✕ buttons.

### Checking off and clearing items

Tap the checkbox on an item to mark it as done (it will be shown with a strikethrough).
Once one or more items are checked, a **"Erledigte löschen (n)"** button appears in the header.
Clicking it removes all checked items from the active list.

## Automations (REST API)

Besides the Ingress UI, the add-on exposes a plain REST API on port `8099` (mapped to
the host) for Home Assistant automations that need direct HTTP access rather than
going through Ingress. Set `api_key` in Configuration to require an `X-API-Key`
header on these requests — without it, anything that can reach the port has full
access. Requests arriving through Ingress are always allowed, with or without a key.

```
GET/POST   /api/v1/lists
GET/POST   /api/v1/categories
PATCH      /api/v1/categories/reorder      (body: [{"id": 1, "sort_order": 0}, ...])
GET/POST   /api/v1/items?list_id=&checked=
PATCH      /api/v1/items/{id}
DELETE     /api/v1/items/{id}
DELETE     /api/v1/items?checked=true&list_id=  (bulk-delete checked items)
```

Example – add an item from an automation:

```
POST http://<host>:8099/api/v1/items
X-API-Key: <your api_key>
Content-Type: application/json

{
  "name": "Milk",
  "quantity": "2L",
  "list_id": 1
}
```

`list_id`/`category_id` are optional; omitting `list_id` leaves the item unassigned
to any list. Full request/response schemas are in the OpenAPI docs at `/docs` on
port `8099`.

## Backup

The SQLite database at `/data/shoppinglist.db` is included in Home Assistant backups automatically.
