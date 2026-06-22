import { useState } from 'react'
import AddTodoForm from './components/AddTodoForm'
import CardDetailPanel from './components/CardDetailPanel'
import KanbanBoard from './components/KanbanBoard'
import PersonsPanel from './components/PersonsPanel'
import TagManager from './components/TagManager'
import WebhookSecretPanel from './components/WebhookSecretPanel'
import { useColumns } from './hooks/useColumns'
import { usePersons } from './hooks/usePersons'
import { useTags } from './hooks/useTags'
import { useTodos } from './hooks/useTodos'

export default function App() {
  const { data: columns = [], isLoading: columnsLoading } = useColumns()
  const { data: tags = [] } = useTags()
  const { data: persons = [] } = usePersons()
  const [mineOnly, setMineOnly] = useState(false)
  const { data: todos = [], isLoading: todosLoading } = useTodos(mineOnly)
  const [editingTodoId, setEditingTodoId] = useState<string | null>(null)

  const loading = columnsLoading || todosLoading
  const sortedColumns = [...columns].sort((a, b) => a.position - b.position)
  const editingTodo = todos.find((t) => t.id === editingTodoId)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-10 bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
          <h1 className="text-lg font-bold text-gray-800">✅ Todo Manager</h1>
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={mineOnly}
              onChange={(e) => setMineOnly(e.target.checked)}
              className="accent-indigo-500"
            />
            Nur meine Aufgaben
          </label>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 pb-8 pt-4 flex flex-col gap-4">
        <div className="max-w-lg flex flex-col gap-4">
          <AddTodoForm columns={sortedColumns} tags={tags} />
          <WebhookSecretPanel />
          <TagManager />
          <PersonsPanel />
        </div>

        {loading && <p className="text-center text-sm text-gray-400 py-4">Laden…</p>}

        {!loading && (
          <KanbanBoard
            columns={sortedColumns}
            todos={todos}
            tags={tags}
            persons={persons}
            onEdit={setEditingTodoId}
          />
        )}
      </main>

      {editingTodo && (
        <CardDetailPanel
          todo={editingTodo}
          columns={sortedColumns}
          tags={tags}
          onClose={() => setEditingTodoId(null)}
        />
      )}
    </div>
  )
}
