import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { Column, Person, Tag, Todo } from '../api/client'
import TodoCard from './TodoCard'

interface Props {
  todo: Todo
  columns: Column[]
  tags: Tag[]
  persons: Person[]
  onEdit: (id: string) => void
}

export default function SortableTodoCard({ todo, columns, tags, persons, onEdit }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: todo.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <li ref={setNodeRef} style={style}>
      <TodoCard
        todo={todo}
        columns={columns}
        tags={tags}
        persons={persons}
        dragHandleAttributes={attributes}
        dragHandleListeners={listeners}
        onEdit={onEdit}
      />
    </li>
  )
}
