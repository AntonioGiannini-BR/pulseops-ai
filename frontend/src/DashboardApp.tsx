import { useEffect, useState } from 'react'
import Dashboard from './pages/Dashboard'
import Tickets from './pages/Tickets'
import Teams from './pages/Teams'
import AICenter from './pages/AICenter'
import './styles/operations.css'
import Sidebar from './components/Sidebar'

import { getDashboardSummary, getCurrentUser } from './services/api'
import type { DashboardSummary } from './types/api'
import type { AuthenticatedUser } from './types/tickets'

const REFRESH_INTERVAL_MS = 30_000

type Page = 'overview' | 'tickets' | 'teams' | 'ai'

const pageNames: Record<Page, string> = {
  overview: 'Visão geral',
  tickets: 'Chamados',
  teams: 'Equipes',
  ai: 'Central de IA',
}

const pageDescriptions: Record<Page, string> = {
  overview: 'Acompanhe sua operação e tome decisões com dados.',
  tickets: 'Gerencie e acompanhe os chamados da operação.',
  teams: 'Visualize equipes e departamentos.',
  ai: 'Inteligência aplicada ao atendimento.',
}

interface DashboardAppProps {
  token: string
  onLogout: () => void
}

export default function DashboardApp({ token, onLogout }: DashboardAppProps) {
  const [currentPage, setCurrentPage] = useState<Page>('overview')
  const [menuOpen, setMenuOpen] = useState(false)

  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [userRole, setUserRole] = useState<AuthenticatedUser['role'] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    void getCurrentUser(token, controller.signal)
      .then((user) => {
        if (controller.signal.aborted) return
        setUserRole(user.role)
        if (user.role === 'solicitante') setCurrentPage('tickets')
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : 'Não foi possível identificar o usuário.')
        }
      })
    return () => controller.abort()
  }, [token])

  useEffect(() => {
    if (userRole === null || userRole === 'solicitante') {
      setSummary(null)
      setLoading(false)
      return
    }

    const controller = new AbortController()
    let timeoutId: ReturnType<typeof setTimeout> | undefined

    setLoading(true)
    setError(null)
    setSummary(null)

    async function carregarIndicadores() {
      try {
        const dados = await getDashboardSummary(
          token,
          controller.signal,
        )

        if (!controller.signal.aborted) {
          setSummary(dados)
          setError(null)
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Não foi possível carregar os indicadores.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)

          timeoutId = setTimeout(() => {
            void carregarIndicadores()
          }, REFRESH_INTERVAL_MS)
        }
      }
    }

    void carregarIndicadores()

    return () => {
      controller.abort()

      if (timeoutId !== undefined) {
        clearTimeout(timeoutId)
      }
    }
  }, [token, userRole])

  function navigate(page: Page) {
    if (userRole === 'solicitante' && page !== 'tickets') return
    setCurrentPage(page)
    setMenuOpen(false)
  }

  return (
    <div className="layout">
      <div className={menuOpen ? 'sidebar-wrapper open' : 'sidebar-wrapper'}>
        <Sidebar
          currentPage={currentPage}
          onNavigate={navigate}
          totalTickets={summary?.total_chamados ?? 0}
          role={userRole ?? 'solicitante'}
        />
      </div>

      <main className="main">
        <header className="topbar">
          <div className="top-left">
            <button
              className="mobile-menu"
              type="button"
              aria-label={menuOpen ? 'Fechar menu' : 'Abrir menu'}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen(!menuOpen)}
            >
              ☰
            </button>

            <span>Workspace</span>
            <span className="breadcrumb">/</span>
            <span>{pageNames[currentPage]}</span>
          </div>

          <div className="top-actions">
            <span className="environment">
              ● {import.meta.env.VITE_APP_ENV === 'production' ? 'Demonstração online' : 'Desenvolvimento'}
            </span>
            <button type="button" className="logout-action" onClick={onLogout}>
              Sair
            </button>
          </div>
        </header>

        <div className="content">
          <section className="page active">
            <div className="page-heading">
              <div>
                <div className="eyebrow">
                  PULSEOPS / {currentPage.toUpperCase()}
                </div>

                <h1>
                  {pageNames[currentPage]}
                  {currentPage === 'overview' && (
                    <span className="wave"> ✦</span>
                  )}
                </h1>

                <p>{pageDescriptions[currentPage]}</p>
              </div>
            </div>

            <div className="status-note" role="status">
              <span>ⓘ</span>{' '}

              {userRole === null
                ? (error ?? 'Verificando permissões da conta...')
                : userRole === 'solicitante'
                  ? 'Você tem acesso aos chamados vinculados à sua conta.'
                  : loading
                    ? 'Carregando indicadores da operação...'
                    : error
                      ? `Erro ao carregar indicadores: ${error}`
                      : 'Indicadores atualizados com dados do PostgreSQL.'}
            </div>

            {userRole !== null && currentPage === 'overview' && (
              <Dashboard
                summary={summary}
                loading={loading}
                token={token}
              />
            )}

            {currentPage === 'tickets' && (
              <Tickets token={token} />
            )}

            {userRole !== null && userRole !== 'solicitante' && currentPage === 'teams' && <Teams token={token} />}
            {userRole !== null && userRole !== 'solicitante' && currentPage === 'ai' && <AICenter token={token} />}
          </section>
        </div>
      </main>
    </div>
  )
}