import { useState } from 'react'
import type { Column, Tag } from '../api/client'
import { useCreateTodo } from '../hooks/useTodos'

const PRIORITY_LABELS = ['Keine', 'Niedrig', 'Mittel', 'Hoch']

interface Props {
  columns: Column[]
  tags: Tag[]
}

export default function AddTodoForm({ columns, tags }: Props) {
  const [title, setTitle] = useState('')
  const [columnId, setColumnId] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [priority, setPriority] = useState(0)
  const [rrule, setRrule] = useState('')
  const [tagIds, setTagIds] = useState<string[]>([])
  const createTodo = useCreateTodo()

  const activeColumnId = columnId || columns[0]?.id

  function toggleTag(id: string) {
    setTagIds((prev) => (prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed || !activeColumnId) return
    createTodo.mutate(
      {
        title: trimmed,
        column_id: activeColumnId,
        due_date: dueDate || undefined,
        priority,
        rrule: rrule.trim() || undefined,
        tag_ids: tagIds,
      },
      {
        onSuccess: () => {
          setTitle('')
          setDueDate('')
          setPriority(0)
          setRrule('')
          setTagIds([])
        },
      },
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-2 p-4 bg-white rounded-xl shadow-sm border border-gray-100"
    >
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Neues Todo…"
        required
        className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
      />
      <div className="flex flex-wrap gap-2">
        <select
          value={activeColumnId ?? ''}
          onChange={(e) => setColumnId(e.target.value)}
          className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        >
          {columns.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <select
          value={priority}
          onChange={(e) => setPriority(Number(e.target.value))}
          className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        >
          {PRIORITY_LABELS.map((label, value) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <input
        type="text"
        value={rrule}
        onChange={(e) => setRrule(e.target.value)}
        placeholder="Wiederholung (RRULE), z.B. FREQ=WEEKLY;BYDAY=MO – optional"
        className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
      />
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <button
              key={tag.id}
              type="button"
              onClick={() => toggleTag(tag.id)}
              className="rounded-full px-2.5 py-1 text-xs font-medium transition-opacity"
              style={{
                backgroundColor: tag.color,
                color: 'white',
                opacity: tagIds.includes(tag.id) ? 1 : 0.35,
              }}
            >
              {tag.name}
            </button>
          ))}
        </div>
      )}
      <button
        type="submit"
        disabled={createTodo.isPending || !title.trim()}
        className="self-end px-5 py-2 rounded-lg bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-600 active:bg-indigo-700 disabled:opacity-50 transition-colors"
      >
        {createTodo.isPending ? '…' : 'Hinzufügen'}
      </button>
    </form>
  )
}
