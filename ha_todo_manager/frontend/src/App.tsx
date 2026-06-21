import AddTodoForm from './components/AddTodoForm'
import ColumnSection from './components/ColumnSection'
import TagManager from './components/TagManager'
import { useColumns } from './hooks/useColumns'
import { useTags } from './hooks/useTags'
import { useTodos } from './hooks/useTodos'

export default function App() {
  const { data: columns = [], isLoading: columnsLoading } = useColumns()
  const { data: tags = [] } = useTags()
  const { data: todos = [], isLoading: todosLoading } = useTodos()

  const loading = columnsLoading || todosLoading
  const sortedColumns = [...columns].sort((a, b) => a.position - b.position)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-10 bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-lg mx-auto flex items-center px-4 py-3">
          <h1 className="text-lg font-bold text-gray-800">✅ Todo Manager</h1>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 pb-8 pt-4 flex flex-col gap-4">
        <AddTodoForm columns={sortedColumns} tags={tags} />
        <TagManager />

        {loading && <p className="text-center text-sm text-gray-400 py-4">Laden…</p>}

        {!loading &&
          sortedColumns.map((column) => (
            <ColumnSection
              key={column.id}
              column={column}
              todos={todos.filter((t) => t.column_id === column.id)}
              columns={sortedColumns}
              tags={tags}
            />
          ))}
      </main>
    </div>
  )
}
