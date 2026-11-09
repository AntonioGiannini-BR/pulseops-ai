import { useState } from 'react'
import Login from './components/Login'
import DashboardApp from './DashboardApp'

export default function App() {
  const [token, setToken] = useState<string | null>(null)

  function handleAuthenticated(accessToken: string) {
    setToken(accessToken)
  }

  if (!token) {
    return <Login onAuthenticated={handleAuthenticated} />
  }

  return <DashboardApp token={token} onLogout={() => setToken(null)} />
}