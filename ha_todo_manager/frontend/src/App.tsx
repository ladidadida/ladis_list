import { useQuery } from '@tanstack/react-query'

// Reads the HA Ingress path injected into index.html at runtime, same
// convention as ha_shopping_list/frontend/src/api/client.ts.
const meta = document.querySelector<HTMLMetaElement>('meta[name="ingress-path"]')
const BASE = (meta?.content ?? '').replace(/\/$/, '')

function fetchHealth(): Promise<{ status: string }> {
  return fetch(`${BASE}/api/health`).then((res) => res.json())
}

export default function App() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
  })

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="rounded-lg bg-white p-8 text-center shadow">
        <h1 className="text-xl font-semibold text-gray-900">Todo Manager</h1>
        <p className="mt-2 text-sm text-gray-500">
          Skeleton — no views implemented yet.
        </p>
        <p className="mt-4 text-sm">
          Backend health:{' '}
          {isLoading && <span className="text-gray-400">checking…</span>}
          {isError && <span className="text-red-600">unreachable</span>}
          {data && <span className="text-green-600">{data.status}</span>}
        </p>
      </div>
    </div>
  )
}
