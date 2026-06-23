import { Navigate } from 'react-router-dom'
import { useBoards } from '../hooks/useBoards'

// `/` always redirects to the first board (by position) — the backend guarantees at
// least one board always exists (seeded on first start), so this only ever shows a
// loading state briefly.
export default function RootRedirect() {
  const { data: boards, isLoading } = useBoards()

  if (isLoading) {
    return <p className="text-center text-sm text-gray-400 py-8">Laden…</p>
  }

  const firstBoard = boards?.[0]
  if (!firstBoard) {
    return <p className="text-center text-sm text-gray-400 py-8">Kein Board gefunden.</p>
  }

  return <Navigate to={`/board/${firstBoard.id}`} replace />
}
