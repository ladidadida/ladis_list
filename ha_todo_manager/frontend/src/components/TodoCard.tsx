import type { Column, Tag, Todo } from '../api/client'
import { useCompleteTodo, useDeleteTodo, useUpdateTodo } from '../hooks/useTodos'

const PRIORITY_LABELS = ['', 'Niedrig', 'Mittel', 'Hoch']
const PRIORITY_COLORS = ['', 'bg-blue-100 text-blue-700', 'bg-amber-100 text-amber-700', 'bg-red-100 text-red-700']

interface Props {
  todo: Todo
  columns: Column[]
  tags: Tag[]
}

export default function TodoCard({ todo, columns, tags }: Props) {
  const update = useUpdateTodo()
  const complete = useCompleteTodo()
  const remove = useDeleteTodo()

  const todoTags = tags.filter((t) => todo.tag_ids.includes(t.id))
  const column = columns.find((c) => c.id === todo.column_id)
  const isDone = column?.is_terminal ?? false

  return (
    <li className="flex items-start gap-3 p-3 bg-white rounded-xl shadow-sm border border-gray-100">
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
        <select
          value={todo.column_id}
          onChange={(e) => update.mutate({ id: todo.id, data: { column_id: e.target.value } })}
          className="mt-2 rounded-lg border border-gray-200 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-400"
        >
          {columns.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <button
        onClick={() => remove.mutate(todo.id)}
        aria-label={`${todo.title} löschen`}
        className="text-gray-300 hover:text-red-400 transition-colors p-1 rounded"
      >
        ✕
      </button>
    </li>
  )
}
