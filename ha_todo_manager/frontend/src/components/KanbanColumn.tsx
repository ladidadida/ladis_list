import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import type { Column, Person, Tag, Todo } from '../api/client'
import SortableTodoCard from './SortableTodoCard'

interface Props {
  column: Column
  todos: Todo[]
  columns: Column[]
  tags: Tag[]
  persons: Person[]
  onEdit: (id: string) => void
  onAddNew: (columnId: string) => void
}

export default function KanbanColumn({
  column,
  todos,
  columns,
  tags,
  persons,
  onEdit,
  onAddNew,
}: Props) {
  const { setNodeRef } = useDroppable({ id: column.id })

  return (
    <section className="flex flex-col gap-2 min-w-[240px] flex-1">
      <h2 className="flex items-center justify-between text-sm font-semibold text-gray-500">
        <span>
          {column.name} <span className="text-gray-300">({todos.length})</span>
        </span>
        <button
          onClick={() => onAddNew(column.id)}
          aria-label={`Neues Todo in ${column.name}`}
          className="text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 rounded-md w-5 h-5 flex items-center justify-center transition-colors"
        >
          +
        </button>
      </h2>
      <SortableContext items={todos.map((t) => t.id)} strategy={verticalListSortingStrategy}>
        <ul ref={setNodeRef} className="flex flex-col gap-2 min-h-[3rem]">
          {todos.map((todo) => (
            <SortableTodoCard
              key={todo.id}
              todo={todo}
              columns={columns}
              tags={tags}
              persons={persons}
              onEdit={onEdit}
            />
          ))}
          {todos.length === 0 && (
            <li className="text-xs text-gray-400 py-3 text-center border border-dashed border-gray-200 rounded-lg">
              Keine Todos
            </li>
          )}
        </ul>
      </SortableContext>
    </section>
  )
}
