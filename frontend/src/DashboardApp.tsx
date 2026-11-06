import { useEffect, useState } from 'react'
import Dashboard from './pages/Dashboard'
import Tickets from './pages/Tickets'
import Sidebar from './components/Sidebar'

import { getDashboardSummary } from './services/api'
import type { DashboardSummary } from './types/api'

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
}

export default function DashboardApp({ token }: DashboardAppProps) {
  const [currentPage, setCurrentPage] = useState<Page>('overview')
  const [menuOpen, setMenuOpen] = useState(false)

  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
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
  }, [token])

  function navigate(page: Page) {
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
              ● Desenvolvimento
            </span>
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

              {loading
                ? 'Carregando indicadores da operação...'
                : error
                  ? `Erro ao carregar indicadores: ${error}`
                  : 'Indicadores atualizados com dados do PostgreSQL.'}
            </div>

            {currentPage === 'overview' && (
              <Dashboard
                summary={summary}
                loading={loading}
                token={token}
              />
            )}

            {currentPage === 'tickets' && (
              <Tickets token={token} />
            )}

            {currentPage !== 'overview' && currentPage !== 'tickets' && (
            <div className="panel">
              <div className="panel-top">
                <div>
                  <h2>
                    {pageNames[currentPage]}
                  </h2>

                  <p>
                    {'Funcionalidade em desenvolvimento.'}
                  </p>
                </div>
              </div>
            </div>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}