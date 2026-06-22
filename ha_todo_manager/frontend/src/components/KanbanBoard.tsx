import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import type { Column, Person, Tag, Todo, TodoUpdate } from '../api/client'
import { useMoveTodo } from '../hooks/useTodos'
import KanbanColumn from './KanbanColumn'

interface Props {
  columns: Column[]
  todos: Todo[]
  tags: Tag[]
  persons: Person[]
  onEdit: (id: string) => void
}

export default function KanbanBoard({ columns, todos, tags, persons, onEdit }: Props) {
  const moveTodo = useMoveTodo()

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(TouchSensor, {
      activationConstraint: { delay: 200, tolerance: 5 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  )

  function todosForColumn(columnId: string): Todo[] {
    return todos.filter((t) => t.column_id === columnId).sort((a, b) => a.position - b.position)
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const activeTodo = todos.find((t) => t.id === active.id)
    if (!activeTodo) return

    // `over` is either another card (drop near it) or an empty column's container id.
    const overTodo = todos.find((t) => t.id === over.id)
    const destColumnId = overTodo ? overTodo.column_id : (over.id as string)

    const destSiblings = todosForColumn(destColumnId).filter((t) => t.id !== activeTodo.id)
    const overIndex = overTodo ? destSiblings.findIndex((t) => t.id === overTodo.id) : -1
    const insertIndex = overIndex === -1 ? destSiblings.length : overIndex

    const newOrder = [
      ...destSiblings.slice(0, insertIndex),
      activeTodo,
      ...destSiblings.slice(insertIndex),
    ]

    const updates: { id: string; data: TodoUpdate }[] = newOrder
      .map((t, position) => ({ todo: t, position }))
      .filter(({ todo, position }) => todo.position !== position || todo.id === activeTodo.id)
      .map(({ todo, position }) => ({
        id: todo.id,
        data:
          todo.id === activeTodo.id ? { position, column_id: destColumnId } : { position },
      }))

    if (updates.length > 0) moveTodo.mutate(updates)
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <div className="flex gap-4 overflow-x-auto pb-2">
        {columns.map((column) => (
          <KanbanColumn
            key={column.id}
            column={column}
            todos={todosForColumn(column.id)}
            columns={columns}
            tags={tags}
            persons={persons}
            onEdit={onEdit}
          />
        ))}
      </div>
    </DndContext>
  )
}
