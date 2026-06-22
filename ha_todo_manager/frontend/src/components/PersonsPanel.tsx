import { useState } from 'react'
import { useCreatePerson, useDeletePerson, usePersons, useSyncPersons } from '../hooks/usePersons'

export default function PersonsPanel() {
  const { data: persons = [] } = usePersons()
  const sync = useSyncPersons()
  const createPerson = useCreatePerson()
  const deletePerson = useDeletePerson()
  const [name, setName] = useState('')

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    createPerson.mutate({ display_name: trimmed }, { onSuccess: () => setName('') })
  }

  return (
    <div className="flex flex-col gap-2 p-4 bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-600">Personen</h2>
        <button
          onClick={() => sync.mutate()}
          disabled={sync.isPending}
          className="text-xs text-indigo-500 hover:text-indigo-600 disabled:opacity-50 transition-colors"
        >
          {sync.isPending ? 'Synchronisiere…' : 'Sync mit Home Assistant'}
        </button>
      </div>
      {sync.isError && (
        <p className="text-xs text-red-500">
          Sync fehlgeschlagen — Home Assistant Supervisor nicht erreichbar?
        </p>
      )}
      {persons.length === 0 ? (
        <p className="text-xs text-gray-400">Noch keine Personen.</p>
      ) : (
        <ul className="flex flex-col gap-1">
          {persons.map((p) => (
            <li key={p.id} className="flex items-center gap-2 text-sm text-gray-700 group">
              <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100 text-[10px] font-semibold text-indigo-700">
                {p.display_name.slice(0, 2).toUpperCase()}
              </span>
              <span className="flex-1">{p.display_name}</span>
              {!p.ha_user_id && !p.ha_person_entity_id && (
                <span className="text-[10px] text-gray-400">manuell</span>
              )}
              <button
                onClick={() => deletePerson.mutate(p.id)}
                aria-label={`${p.display_name} löschen`}
                className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-400 transition-opacity p-1 rounded"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={handleCreate} className="flex gap-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Neue Person (ohne HA-Konto)…"
          className="flex-1 rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <button
          type="submit"
          disabled={createPerson.isPending || !name.trim()}
          className="px-3 py-1.5 rounded-lg bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-600 disabled:opacity-50 transition-colors"
        >
          {createPerson.isPending ? '…' : '+'}
        </button>
      </form>
    </div>
  )
}
