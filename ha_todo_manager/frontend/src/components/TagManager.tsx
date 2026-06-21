import { useState } from 'react'
import { useCreateTag, useDeleteTag, useTags } from '../hooks/useTags'

export default function TagManager() {
  const { data: tags = [] } = useTags()
  const createTag = useCreateTag()
  const deleteTag = useDeleteTag()
  const [name, setName] = useState('')
  const [color, setColor] = useState('#6366f1')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    createTag.mutate({ name: trimmed, color }, { onSuccess: () => setName('') })
  }

  return (
    <div className="flex flex-col gap-2 p-4 bg-white rounded-xl shadow-sm border border-gray-100">
      <h2 className="text-sm font-semibold text-gray-600">Tags</h2>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <span
            key={tag.id}
            className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium text-white"
            style={{ backgroundColor: tag.color }}
          >
            {tag.name}
            <button
              onClick={() => deleteTag.mutate(tag.id)}
              aria-label={`${tag.name} löschen`}
              className="hover:opacity-75"
            >
              ✕
            </button>
          </span>
        ))}
        {tags.length === 0 && <span className="text-xs text-gray-400">Noch keine Tags</span>}
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Neuer Tag…"
          className="flex-1 rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <input
          type="color"
          value={color}
          onChange={(e) => setColor(e.target.value)}
          className="h-9 w-9 rounded-lg border border-gray-200 cursor-pointer"
          aria-label="Tag-Farbe"
        />
        <button
          type="submit"
          disabled={createTag.isPending || !name.trim()}
          className="px-3 py-1.5 rounded-lg bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-600 disabled:opacity-50 transition-colors"
        >
          {createTag.isPending ? '…' : '+'}
        </button>
      </form>
    </div>
  )
}
