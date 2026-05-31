// API base URL – reads the HA Ingress path injected into index.html at runtime.
const meta = document.querySelector<HTMLMetaElement>('meta[name="ingress-path"]')
const BASE = (meta?.content ?? '').replace(/\/$/, '')

export const API_BASE = `${BASE}/api/v1`

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ShoppingList {
  id: number
  name: string
  sort_order: number
}

export interface ShoppingListCreate {
  name: string
  sort_order?: number
}

export interface Category {
  id: number
  name: string
  sort_order: number
}

export interface Item {
  id: number
  name: string
  quantity: string | null
  checked: boolean
  category_id: number | null
  list_id: number | null
}

export interface ItemCreate {
  name: string
  quantity?: string
  category_id?: number | null
  list_id?: number | null
}

export interface ItemUpdate {
  name?: string
  quantity?: string | null
  checked?: boolean
  category_id?: number | null
  list_id?: number | null
}

export interface CategoryCreate {
  name: string
  sort_order?: number
}

export interface CategoryReorderItem {
  id: number
  sort_order: number
}

// ─── Fetch helpers ────────────────────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status}: ${text}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// ─── Shopping Lists ───────────────────────────────────────────────────────────

export const fetchLists = () => request<ShoppingList[]>('/lists')

export const createList = (data: ShoppingListCreate) =>
  request<ShoppingList>('/lists', { method: 'POST', body: JSON.stringify(data) })

export const deleteList = (id: number) =>
  request<void>(`/lists/${id}`, { method: 'DELETE' })

// ─── Categories ───────────────────────────────────────────────────────────────

export const fetchCategories = () => request<Category[]>('/categories')

export const createCategory = (data: CategoryCreate) =>
  request<Category>('/categories', { method: 'POST', body: JSON.stringify(data) })

export const deleteCategory = (id: number) =>
  request<void>(`/categories/${id}`, { method: 'DELETE' })

export const reorderCategories = (items: CategoryReorderItem[]) =>
  request<void>('/categories/reorder', { method: 'PATCH', body: JSON.stringify(items) })

// ─── Items ────────────────────────────────────────────────────────────────────

export const fetchItems = (listId?: number) =>
  request<Item[]>(listId !== undefined ? `/items?list_id=${listId}` : '/items')

export const createItem = (data: ItemCreate) =>
  request<Item>('/items', { method: 'POST', body: JSON.stringify(data) })

export const updateItem = (id: number, data: ItemUpdate) =>
  request<Item>(`/items/${id}`, { method: 'PATCH', body: JSON.stringify(data) })

export const deleteItem = (id: number) =>
  request<void>(`/items/${id}`, { method: 'DELETE' })

export const deleteCheckedItems = (listId?: number) =>
  request<void>(
    listId !== undefined ? `/items?checked=true&list_id=${listId}` : '/items?checked=true',
    { method: 'DELETE' },
  )
