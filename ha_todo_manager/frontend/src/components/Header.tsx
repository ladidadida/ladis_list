import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'

interface Props {
  children?: ReactNode
}

export default function Header({ children }: Props) {
  const location = useLocation()
  const onSettings = location.pathname === '/settings'

  return (
    <header className="sticky top-0 z-10 bg-white border-b border-gray-100 shadow-sm">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
        <h1 className="text-lg font-bold text-gray-800">✅ Todo Manager</h1>
        <div className="flex items-center gap-4">
          {children}
          <Link
            to={onSettings ? '/' : '/settings'}
            className="text-sm text-gray-500 hover:text-indigo-600 transition-colors"
          >
            {onSettings ? '← Board' : '⚙️ Einstellungen'}
          </Link>
        </div>
      </div>
    </header>
  )
}
