import { useEffect, useState } from 'react'
import Login from './components/Login'
import DashboardApp from './DashboardApp'

export default function App() {
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    function expireSession() { setToken(null) }
    window.addEventListener('pulseops:session-expired', expireSession)
    return () => window.removeEventListener('pulseops:session-expired', expireSession)
  }, [])

  function handleAuthenticated(accessToken: string) {
    setToken(accessToken)
  }

  if (!token) {
    return <Login onAuthenticated={handleAuthenticated} />
  }

  return <DashboardApp token={token} onLogout={() => setToken(null)} />
}