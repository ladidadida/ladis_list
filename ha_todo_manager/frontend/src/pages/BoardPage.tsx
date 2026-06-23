import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import CardDetailPanel from '../components/CardDetailPanel'
import Header from '../components/Header'
import KanbanBoard from '../components/KanbanBoard'
import { useBoards } from '../hooks/useBoards'
import { useColumns } from '../hooks/useColumns'
import { usePersons } from '../hooks/usePersons'
import { useTags } from '../hooks/useTags'
import { useTodos } from '../hooks/useTodos'

type Panel = { mode: 'edit'; todoId: string } | { mode: 'create'; columnId: string } | null

export default function BoardPage() {
  const { boardId = '' } = useParams<{ boardId: string }>()
  const navigate = useNavigate()
  const { data: boards = [] } = useBoards()
  const { data: columns = [], isLoading: columnsLoading } = useColumns(boardId)
  const { data: tags = [] } = useTags()
  const { data: persons = [] } = usePersons()
  const [mineOnly, setMineOnly] = useState(false)
  const { data: todos = [], isLoading: todosLoading } = useTodos(boardId, mineOnly)
  const [panel, setPanel] = useState<Panel>(null)

  const loading = columnsLoading || todosLoading
  const sortedColumns = [...columns].sort((a, b) => a.position - b.position)
  const editingTodo = panel?.mode === 'edit' ? todos.find((t) => t.id === panel.todoId) : undefined

  return (
    <div className="min-h-screen bg-gray-50">
      <Header>
        {boards.length > 1 && (
          <select
            value={boardId}
            onChange={(e) => navigate(`/board/${e.target.value}`)}
            className="rounded-lg border border-gray-200 px-2 py-1 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            {boards.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        )}
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={mineOnly}
            onChange={(e) => setMineOnly(e.target.checked)}
            className="accent-indigo-500"
          />
          Nur meine Aufgaben
        </label>
      </Header>

      <main className="max-w-6xl mx-auto px-4 pb-8 pt-4">
        {loading && <p className="text-center text-sm text-gray-400 py-4">Laden…</p>}

        {!loading && (
          <KanbanBoard
            columns={sortedColumns}
            todos={todos}
            tags={tags}
            persons={persons}
            onEdit={(todoId) => setPanel({ mode: 'edit', todoId })}
            onAddNew={(columnId) => setPanel({ mode: 'create', columnId })}
          />
        )}
      </main>

      {panel?.mode === 'edit' && editingTodo && (
        <CardDetailPanel
          todo={editingTodo}
          columns={sortedColumns}
          tags={tags}
          onClose={() => setPanel(null)}
        />
      )}
      {panel?.mode === 'create' && (
        <CardDetailPanel
          defaultColumnId={panel.columnId}
          columns={sortedColumns}
          tags={tags}
          onClose={() => setPanel(null)}
        />
      )}
    </div>
  )
}
