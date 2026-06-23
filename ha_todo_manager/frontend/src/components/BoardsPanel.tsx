import { useState } from 'react'
import { useBoards, useCreateBoard, useDeleteBoard, useUpdateBoard } from '../hooks/useBoards'

export default function BoardsPanel() {
  const { data: boards = [] } = useBoards()
  const createBoard = useCreateBoard()
  const updateBoard = useUpdateBoard()
  const deleteBoard = useDeleteBoard()
  const [name, setName] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingName, setEditingName] = useState('')

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    createBoard.mutate({ name: trimmed }, { onSuccess: () => setName('') })
  }

  function startEdit(id: string, currentName: string) {
    setEditingId(id)
    setEditingName(currentName)
  }

  function saveEdit() {
    if (!editingId) return
    const trimmed = editingName.trim()
    if (trimmed) updateBoard.mutate({ id: editingId, data: { name: trimmed } })
    setEditingId(null)
  }

  function handleDelete(id: string, boardName: string) {
    if (boards.length <= 1) return
    const ok = window.confirm(
      `"${boardName}" inklusive aller Spalten und Aufgaben unwiderruflich löschen?`,
    )
    if (!ok) return
    deleteBoard.mutate(id)
  }

  return (
    <div className="flex flex-col gap-2 p-4 bg-white rounded-xl shadow-sm border border-gray-100">
      <h2 className="text-sm font-semibold text-gray-600">Boards</h2>
      {deleteBoard.isError && <p className="text-xs text-red-500">Löschen fehlgeschlagen.</p>}
      <ul className="flex flex-col gap-1">
        {boards.map((b) => (
          <li key={b.id} className="flex items-center gap-2 text-sm text-gray-700 group">
            {editingId === b.id ? (
              <input
                type="text"
                value={editingName}
                onChange={(e) => setEditingName(e.target.value)}
                onBlur={saveEdit}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') saveEdit()
                  if (e.key === 'Escape') setEditingId(null)
                }}
                autoFocus
                className="flex-1 rounded-lg border border-indigo-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            ) : (
              <span className="flex-1">{b.name}</span>
            )}
            <button
              onClick={() => startEdit(b.id, b.name)}
              aria-label={`${b.name} umbenennen`}
              className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-indigo-400 transition-opacity p-1 rounded"
            >
              ✏️
            </button>
            <button
              onClick={() => handleDelete(b.id, b.name)}
              disabled={boards.length <= 1}
              aria-label={`${b.name} löschen`}
              className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-400 transition-opacity p-1 rounded disabled:opacity-0"
            >
              ✕
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={handleCreate} className="flex gap-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Neues Board…"
          className="flex-1 rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <button
          type="submit"
          disabled={createBoard.isPending || !name.trim()}
          className="px-3 py-1.5 rounded-lg bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-600 disabled:opacity-50 transition-colors"
        >
          {createBoard.isPending ? '…' : '+'}
        </button>
      </form>
    </div>
  )
}
