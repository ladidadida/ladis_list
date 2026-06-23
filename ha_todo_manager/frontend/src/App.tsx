import { HashRouter, Route, Routes } from 'react-router-dom'
import BoardPage from './pages/BoardPage'
import RootRedirect from './pages/RootRedirect'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/board/:boardId" element={<BoardPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </HashRouter>
  )
}
