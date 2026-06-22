import type { DraggableAttributes, DraggableSyntheticListeners } from '@dnd-kit/core'
import type { Column, Person, Tag, Todo } from '../api/client'
import { useCompleteTodo, useDeleteTodo } from '../hooks/useTodos'

const PRIORITY_LABELS = ['', 'Niedrig', 'Mittel', 'Hoch']
const PRIORITY_COLORS = ['', 'bg-blue-100 text-blue-700', 'bg-amber-100 text-amber-700', 'bg-red-100 text-red-700']

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('')
}

interface Props {
  todo: Todo
  columns: Column[]
  tags: Tag[]
  persons: Person[]
  dragHandleAttributes?: DraggableAttributes
  dragHandleListeners?: DraggableSyntheticListeners
  onEdit?: (id: string) => void
}

export default function TodoCard({
  todo,
  columns,
  tags,
  persons,
  dragHandleAttributes,
  dragHandleListeners,
  onEdit,
}: Props) {
  const complete = useCompleteTodo()
  const remove = useDeleteTodo()

  const todoTags = tags.filter((t) => todo.tag_ids.includes(t.id))
  const column = columns.find((c) => c.id === todo.column_id)
  const isDone = column?.is_terminal ?? false
  const assignee = persons.find((p) => p.id === todo.assignee_id)

  return (
    <div className="flex items-start gap-2 p-3 bg-white rounded-xl shadow-sm border border-gray-100">
      {dragHandleAttributes && (
        <button
          {...dragHandleAttributes}
          {...dragHandleListeners}
          aria-label={`${todo.title} verschieben`}
          className="mt-0.5 text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing p-1 touch-none flex-shrink-0"
        >
          ⠿
        </button>
      )}
      <button
        onClick={() => complete.mutate(todo.id)}
        disabled={complete.isPending || isDone}
        aria-label={`${todo.title} erledigt`}
        className={`mt-0.5 w-5 h-5 rounded-full border-2 flex-shrink-0 transition-colors ${
          isDone ? 'bg-green-400 border-green-400' : 'border-gray-300 hover:border-indigo-400'
        }`}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {assignee && (
            <span
              title={assignee.display_name}
              className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 text-[10px] font-semibold text-indigo-700"
            >
              {initials(assignee.display_name)}
            </span>
          )}
          <span className={`text-sm ${isDone ? 'line-through text-gray-400' : 'text-gray-800'}`}>
            {todo.title}
          </span>
          {todo.rrule && <span title={`Wiederholt sich: ${todo.rrule}`}>🔁</span>}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs">
          {todo.due_date && <span className="text-gray-400">📅 {todo.due_date}</span>}
          {todo.priority > 0 && (
            <span className={`rounded-full px-2 py-0.5 font-medium ${PRIORITY_COLORS[todo.priority]}`}>
              {PRIORITY_LABELS[todo.priority]}
            </span>
          )}
          {todoTags.map((tag) => (
            <span
              key={tag.id}
              className="rounded-full px-2 py-0.5 font-medium text-white"
              style={{ backgroundColor: tag.color }}
            >
              {tag.name}
            </span>
          ))}
        </div>
      </div>
      {onEdit && (
        <button
          onClick={() => onEdit(todo.id)}
          aria-label={`${todo.title} bearbeiten`}
          className="text-gray-300 hover:text-indigo-400 transition-colors p-1 rounded"
        >
          ✏️
        </button>
      )}
      <button
        onClick={() => remove.mutate(todo.id)}
        aria-label={`${todo.title} löschen`}
        className="text-gray-300 hover:text-red-400 transition-colors p-1 rounded"
      >
        ✕
      </button>
    </div>
  )
}
