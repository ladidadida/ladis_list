import type { Column, Tag, Todo } from '../api/client'
import TodoCard from './TodoCard'

interface Props {
  column: Column
  todos: Todo[]
  columns: Column[]
  tags: Tag[]
}

export default function ColumnSection({ column, todos, columns, tags }: Props) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-gray-500">
        {column.name} <span className="text-gray-300">({todos.length})</span>
      </h2>
      {todos.length === 0 ? (
        <p className="text-xs text-gray-400 py-2">Keine Todos</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {todos.map((todo) => (
            <TodoCard key={todo.id} todo={todo} columns={columns} tags={tags} />
          ))}
        </ul>
      )}
    </section>
  )
}
