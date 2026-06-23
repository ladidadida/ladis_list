import BoardsPanel from '../components/BoardsPanel'
import Header from '../components/Header'
import PersonsPanel from '../components/PersonsPanel'
import TagManager from '../components/TagManager'
import WebhookSecretPanel from '../components/WebhookSecretPanel'

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-lg mx-auto px-4 pb-8 pt-4 flex flex-col gap-4">
        <BoardsPanel />
        <WebhookSecretPanel />
        <TagManager />
        <PersonsPanel />
      </main>
    </div>
  )
}
