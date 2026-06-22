// API base URL – reads the HA Ingress path injected into index.html at runtime.
const meta = document.querySelector<HTMLMetaElement>('meta[name="ingress-path"]')
const BASE = (meta?.content ?? '').replace(/\/$/, '')

export const API_BASE = `${BASE}/api`

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Column {
  id: string
  name: string
  position: number
  is_terminal: boolean
  status_key: string
}

export interface Tag {
  id: string
  name: string
  color: string
}

export interface TagCreate {
  name: string
  color: string
}

export interface Person {
  id: string
  display_name: string
  ha_user_id: string | null
  ha_person_entity_id: string | null
  avatar_url: string | null
}

export interface PersonCreate {
  display_name: string
  avatar_url?: string | null
}

export interface Todo {
  id: string
  title: string
  description: string | null
  column_id: string
  assignee_id: string | null
  due_date: string | null
  priority: number
  position: number
  rrule: string | null
  next_due: string | null
  recurrence_parent_id: string | null
  source: 'manual' | 'ha_webhook'
  source_ref: string | null
  created_at: string
  updated_at: string
  tag_ids: string[]
}

export interface TodoCreate {
  title: string
  description?: string | null
  column_id: string
  assignee_id?: string | null
  due_date?: string | null
  priority?: number
  position?: number
  rrule?: string | null
  tag_ids?: string[]
}

export interface TodoUpdate {
  title?: string
  description?: string | null
  column_id?: string
  assignee_id?: string | null
  due_date?: string | null
  priority?: number
  position?: number
  rrule?: string | null
  tag_ids?: string[] | null
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

// ─── Columns ──────────────────────────────────────────────────────────────────

export const fetchColumns = () => request<Column[]>('/columns')

// ─── Tags ─────────────────────────────────────────────────────────────────────

export const fetchTags = () => request<Tag[]>('/tags')

export const createTag = (data: TagCreate) =>
  request<Tag>('/tags', { method: 'POST', body: JSON.stringify(data) })

export const deleteTag = (id: string) => request<void>(`/tags/${id}`, { method: 'DELETE' })

// ─── Persons ──────────────────────────────────────────────────────────────────

export const fetchPersons = () => request<Person[]>('/persons')

export const createPerson = (data: PersonCreate) =>
  request<Person>('/persons', { method: 'POST', body: JSON.stringify(data) })

export const deletePerson = (id: string) => request<void>(`/persons/${id}`, { method: 'DELETE' })

export const syncPersons = () => request<{ synced: number }>('/persons/sync', { method: 'POST' })

// ─── Webhook ──────────────────────────────────────────────────────────────────

// 404 means "nothing to reveal" (already shown once, or explicitly configured) —
// that's a normal outcome here, not an error, so this bypasses the generic
// request() helper which throws on any non-2xx response.
export async function fetchWebhookSecret(): Promise<string | null> {
  const res = await fetch(`${API_BASE}/webhook/secret`)
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`)
  const data = (await res.json()) as { secret: string }
  return data.secret
}

// ─── Todos ────────────────────────────────────────────────────────────────────

export const fetchTodos = (mine?: boolean) =>
  request<Todo[]>(mine ? '/todos?mine=true' : '/todos')

export const createTodo = (data: TodoCreate) =>
  request<Todo>('/todos', { method: 'POST', body: JSON.stringify(data) })

export const updateTodo = (id: string, data: TodoUpdate) =>
  request<Todo>(`/todos/${id}`, { method: 'PATCH', body: JSON.stringify(data) })

export const deleteTodo = (id: string) => request<void>(`/todos/${id}`, { method: 'DELETE' })

export const completeTodo = (id: string) =>
  request<Todo>(`/todos/${id}/complete`, { method: 'POST' })
