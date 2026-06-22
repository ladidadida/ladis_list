import { useState } from 'react'
import type { Column, Tag, Todo } from '../api/client'
import { usePersons } from '../hooks/usePersons'
import { useDeleteTodo, useUpdateTodo } from '../hooks/useTodos'
import { buildRrule, parseRrulePreset, WEEKDAY_LABELS, WEEKDAYS, type RrulePreset } from '../lib/rrule'

const PRIORITY_LABELS = ['Keine', 'Niedrig', 'Mittel', 'Hoch']

interface Props {
  todo: Todo
  columns: Column[]
  tags: Tag[]
  onClose: () => void
}

export default function CardDetailPanel({ todo, columns, tags, onClose }: Props) {
  const update = useUpdateTodo()
  const remove = useDeleteTodo()
  const { data: persons = [] } = usePersons()

  const [title, setTitle] = useState(todo.title)
  const [description, setDescription] = useState(todo.description ?? '')
  const [columnId, setColumnId] = useState(todo.column_id)
  const [assigneeId, setAssigneeId] = useState(todo.assignee_id ?? '')
  const [dueDate, setDueDate] = useState(todo.due_date ?? '')
  const [priority, setPriority] = useState(todo.priority)
  const [tagIds, setTagIds] = useState<string[]>(todo.tag_ids)
  const [preset, setPreset] = useState<RrulePreset>(() => parseRrulePreset(todo.rrule))

  function toggleTag(id: string) {
    setTagIds((prev) => (prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]))
  }

  function toggleWeekday(day: string) {
    if (preset.kind !== 'weekly') return
    setPreset({
      kind: 'weekly',
      days: preset.days.includes(day) ? preset.days.filter((d) => d !== day) : [...preset.days, day],
    })
  }

  function handlePresetKindChange(kind: RrulePreset['kind']) {
    if (kind === 'weekly') setPreset({ kind: 'weekly', days: [] })
    else if (kind === 'custom') setPreset({ kind: 'custom', raw: todo.rrule ?? '' })
    else if (kind === 'none') setPreset({ kind: 'none' })
    else if (kind === 'daily') setPreset({ kind: 'daily' })
    else if (kind === 'monthly') setPreset({ kind: 'monthly' })
    else setPreset({ kind: 'yearly' })
  }

  function handleSave(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) return
    update.mutate(
      {
        id: todo.id,
        data: {
          title: trimmed,
          description: description.trim() || null,
          column_id: columnId,
          assignee_id: assigneeId || null,
          due_date: dueDate || null,
          priority,
          rrule: buildRrule(preset),
          tag_ids: tagIds,
        },
      },
      { onSuccess: onClose },
    )
  }

  function handleDelete() {
    remove.mutate(todo.id, { onSuccess: onClose })
  }

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <aside className="relative z-50 w-full max-w-md bg-white h-full shadow-xl flex flex-col overflow-y-auto">
        <header className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Todo bearbeiten</h2>
          <button
            onClick={onClose}
            aria-label="Schließen"
            className="text-gray-400 hover:text-gray-600 text-lg p-1"
          >
            ✕
          </button>
        </header>

        <form onSubmit={handleSave} className="flex-1 flex flex-col gap-3 p-4">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Titel"
            required
            className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Beschreibung…"
            rows={4}
            className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <div className="flex gap-2">
            <select
              value={columnId}
              onChange={(e) => setColumnId(e.target.value)}
              className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              {columns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
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
          <div className="flex gap-2">
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <select
              value={assigneeId}
              onChange={(e) => setAssigneeId(e.target.value)}
              className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              <option value="">Niemand zugewiesen</option>
              {persons.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.display_name}
                </option>
              ))}
            </select>
          </div>

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

          <div className="flex flex-col gap-2 rounded-lg border border-gray-100 p-3">
            <span className="text-xs font-semibold text-gray-500">Wiederholung</span>
            <select
              value={preset.kind}
              onChange={(e) => handlePresetKindChange(e.target.value as RrulePreset['kind'])}
              className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              <option value="none">Keine</option>
              <option value="daily">Täglich</option>
              <option value="weekly">Wöchentlich</option>
              <option value="monthly">Monatlich</option>
              <option value="yearly">Jährlich</option>
              <option value="custom">Eigene (RRULE)</option>
            </select>
            {preset.kind === 'weekly' && (
              <div className="flex gap-1 flex-wrap">
                {WEEKDAYS.map((day) => (
                  <button
                    key={day}
                    type="button"
                    onClick={() => toggleWeekday(day)}
                    className={`rounded-lg px-2 py-1 text-xs font-medium border transition-colors ${
                      preset.days.includes(day)
                        ? 'bg-indigo-500 text-white border-indigo-500'
                        : 'border-gray-200 text-gray-500 hover:border-indigo-300'
                    }`}
                  >
                    {WEEKDAY_LABELS[day]}
                  </button>
                ))}
              </div>
            )}
            {preset.kind === 'custom' && (
              <input
                type="text"
                value={preset.raw}
                onChange={(e) => setPreset({ kind: 'custom', raw: e.target.value })}
                placeholder="z.B. FREQ=WEEKLY;BYDAY=MO"
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            )}
          </div>

          <div className="mt-auto flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleDelete}
              disabled={remove.isPending}
              className="px-3 py-1.5 rounded-lg text-red-400 hover:text-red-600 text-sm transition-colors disabled:opacity-50"
            >
              Löschen
            </button>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 rounded-lg text-gray-400 hover:text-gray-600 text-sm transition-colors"
              >
                Abbrechen
              </button>
              <button
                type="submit"
                disabled={update.isPending || !title.trim()}
                className="px-4 py-1.5 rounded-lg bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-600 disabled:opacity-50 transition-colors"
              >
                {update.isPending ? '…' : 'Speichern'}
              </button>
            </div>
          </div>
        </form>
      </aside>
    </div>
  )
}
