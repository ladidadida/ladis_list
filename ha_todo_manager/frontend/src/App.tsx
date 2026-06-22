import { HashRouter, Route, Routes } from 'react-router-dom'
import BoardPage from './pages/BoardPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<BoardPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </HashRouter>
  )
}
