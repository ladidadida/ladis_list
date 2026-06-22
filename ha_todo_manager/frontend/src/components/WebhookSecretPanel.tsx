import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchWebhookSecret } from '../api/client'

// Calls GET /api/webhook/secret once; the backend only reveals the
// auto-generated secret the first time it's ever requested (or never, if an
// explicit ha_webhook_secret option is configured) — so `secret` being null/
// undefined is the normal steady state, not an error.
export default function WebhookSecretPanel() {
  const [copied, setCopied] = useState(false)
  const { data: secret, isLoading } = useQuery({
    queryKey: ['webhook-secret'],
    queryFn: fetchWebhookSecret,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })

  if (isLoading || !secret) return null

  function handleCopy() {
    if (!secret) return
    navigator.clipboard?.writeText(secret).then(() => setCopied(true))
  }

  return (
    <div className="flex flex-col gap-2 p-4 bg-amber-50 rounded-xl shadow-sm border border-amber-200">
      <h2 className="text-sm font-semibold text-amber-800">⚠️ Webhook-Secret</h2>
      <p className="text-xs text-amber-700">
        Wird nur dieses eine Mal angezeigt — jetzt für HA-Automationen speichern!
      </p>
      <div className="flex items-center gap-2">
        <code className="flex-1 truncate rounded-lg border border-amber-200 bg-white px-2 py-1.5 text-xs text-gray-700">
          {secret}
        </code>
        <button
          onClick={handleCopy}
          className="px-3 py-1.5 rounded-lg bg-amber-500 text-white text-xs font-medium hover:bg-amber-600 transition-colors"
        >
          {copied ? 'Kopiert!' : 'Kopieren'}
        </button>
      </div>
    </div>
  )
}
