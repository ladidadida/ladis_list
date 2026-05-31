import { useState } from 'react'
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
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useCategories, useCreateCategory, useDeleteCategory, useReorderCategories } from '../hooks/useShoppingList'
import type { Category } from '../api/client'

// ─── Sortable row ─────────────────────────────────────────────────────────────

function SortableCategoryRow({
  category,
  onDelete,
}: {
  category: Category
  onDelete: (id: number) => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: category.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className="flex items-center justify-between py-2"
    >
      {/* Drag handle */}
      <button
        {...attributes}
        {...listeners}
        aria-label={`${category.name} verschieben`}
        className="text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing p-1 mr-1 touch-none"
      >
        ⠿
      </button>
      <span className="flex-1 text-sm text-gray-700">{category.name}</span>
      <button
        onClick={() => onDelete(category.id)}
        aria-label={`${category.name} löschen`}
        className="text-gray-300 hover:text-red-400 text-sm p-1 rounded transition-colors"
      >
        ✕
      </button>
    </li>
  )
}

// ─── Drawer ───────────────────────────────────────────────────────────────────

interface Props {
  onClose: () => void
}

export default function CategoryDrawer({ onClose }: Props) {
  const { data: categories = [] } = useCategories()
  const createCategory = useCreateCategory()
  const deleteCategory = useDeleteCategory()
  const reorderCategories = useReorderCategories()
  const [name, setName] = useState('')

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(TouchSensor, {
      activationConstraint: { delay: 200, tolerance: 5 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  )

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    const maxOrder = categories.reduce((m, c) => Math.max(m, c.sort_order), -1)
    createCategory.mutate({ name: trimmed, sort_order: maxOrder + 1 }, { onSuccess: () => setName('') })
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const oldIndex = categories.findIndex((c) => c.id === active.id)
    const newIndex = categories.findIndex((c) => c.id === over.id)
    const reordered = arrayMove(categories, oldIndex, newIndex)

    reorderCategories.mutate(
      reordered.map((c, i) => ({ id: c.id, sort_order: i })),
    )
  }

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      {/* Panel */}
      <aside className="relative z-50 w-72 bg-white h-full shadow-xl flex flex-col">
        <header className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Kategorien</h2>
          <button
            onClick={onClose}
            aria-label="Schließen"
            className="text-gray-400 hover:text-gray-600 text-lg p-1"
          >
            ✕
          </button>
        </header>

        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={categories.map((c) => c.id)} strategy={verticalListSortingStrategy}>
            <ul className="flex-1 overflow-y-auto divide-y divide-gray-50 px-4 py-2">
              {categories.map((c) => (
                <SortableCategoryRow
                  key={c.id}
                  category={c}
                  onDelete={(id) => deleteCategory.mutate(id)}
                />
              ))}
            </ul>
          </SortableContext>
        </DndContext>

        <form onSubmit={handleCreate} className="p-4 border-t border-gray-100 flex gap-2">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Neue Kategorie…"
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <button
            type="submit"
            disabled={createCategory.isPending}
            className="px-4 py-2 rounded-lg bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-600 disabled:opacity-50 transition-colors"
          >
            +
          </button>
        </form>
      </aside>
    </div>
  )
}
