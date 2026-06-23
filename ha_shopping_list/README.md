# ha-shopping-list

A fast, mobile-friendly shopping list add-on for Home Assistant.

## Features

- **Multiple lists** – create one list per store or purpose; switch with a single tap
- **Category organisation** – assign items to categories (e.g. Dairy, Vegetables); items are grouped and sorted automatically, and categories can be drag-reordered
- **Inline item editing** – tap the ✏️ icon on any item to edit its name, quantity, or category without leaving the page
- **Quick-add per category** – tap **+** next to a category heading to add directly into that category
- **Check off & clear** – tick items as you shop; delete individually or use "Erledigte löschen" to bulk-remove finished items
- **Automation-friendly** – a REST API on port `8099`, separate from the Ingress UI, optionally protected by an `api_key` (see [DOCS.md](DOCS.md))
- **Persistent storage** – all data lives in `/data/shoppinglist.db` (a plain SQLite file), survives restarts and is included in HA backups

## Installation

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**.
2. Click the three-dot menu (⋮) → **Repositories** and add your repository URL.
3. Find **Shopping List** in the store, click **Install**.
4. Start the add-on. It appears in the sidebar as **Shopping List** (🛒).

## Usage

### Lists

Click the **🛒 list name** in the header to open the list drawer.  
From there you can create new lists or delete existing ones (the last list cannot be deleted).

### Categories

Click **🏷️ Kategorien** in the header to open the category manager.  
Categories are global (shared across all lists). Create or delete them here, or drag
the **⠿** handle to reorder.

### Items

- **Add:** Use the form at the top of the page (name, optional quantity, optional category).
- **Quick-add per category:** Click the **+** button next to any category heading.
- **Edit:** Hover over an item and click **✏️** to change its name, quantity, or category.
- **Check off:** Tap the checkbox to mark an item as done (strikethrough).
- **Delete:** Hover over an item and click **✕**, or use "Erledigte löschen" to remove all checked items at once.

## Configuration

| Option | Default | Description |
|---|---|---|
| `log_level` | `info` | Verbosity: `trace`, `debug`, `info`, `warning`, `error`, `fatal` |
| `api_key` | `""` (disabled) | Protects the REST API on port `8099` for requests not coming through Ingress; see [DOCS.md](DOCS.md) |

## Backup & data

The SQLite database is stored at `/data/shoppinglist.db`. Home Assistant backs this up automatically together with all other add-on data.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13 · FastAPI · SQLModel |
| Frontend | React 19 · Vite · Tailwind CSS · TanStack Query |
| Packaging | `uv` · `hatchling` · multi-stage Docker build |
| Runtime | HA Ingress, plus an optional `api_key`-protected REST API on port `8099` |

## License

MIT – see [LICENSE](LICENSE).
