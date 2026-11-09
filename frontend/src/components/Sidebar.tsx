type Page = 'overview' | 'tickets' | 'teams' | 'ai' | 'users' | 'account'

interface SidebarProps {
  currentPage: Page
  onNavigate: (page: Page) => void
  totalTickets?: number
  role: 'admin' | 'analista' | 'solicitante'
}

export default function Sidebar({
  currentPage,
  onNavigate,
  totalTickets = 0,
  role,
}: SidebarProps) {
  const menuItems: {
    page: Page
    label: string
    icon: string
  }[] = [
    { page: 'overview', label: 'Visão geral', icon: '▦' },
    { page: 'tickets', label: 'Chamados', icon: '▤' },
    { page: 'teams', label: 'Equipes', icon: '♙' },
    { page: 'ai', label: 'Central de IA', icon: '✧' },
    { page: 'users', label: 'Usuários', icon: '♙' },
    { page: 'account', label: 'Minha conta', icon: '◇' },
  ]

  return (
    <aside className="sidebar" id="sidebar">
      <a
        className="brand"
        href="#overview"
        onClick={(event) => {
          event.preventDefault()
          onNavigate('overview')
        }}
        aria-label="PulseOps AI, início"
      >
        <span className="brand-symbol">◈</span>
        <span>
          pulse<span className="brand-strong">ops</span>
          <small>AI</small>
        </span>
      </a>

      <div className="brand-subtitle">
        PLATAFORMA INTELIGENTE
      </div>

      <div className="nav-label">MENU PRINCIPAL</div>

      <nav className="nav" aria-label="Navegação principal">
        {menuItems.filter((item) => item.page === 'account' || (role === 'admin') || (role === 'analista' && item.page !== 'users') || (role === 'solicitante' && item.page === 'tickets')).map((item) => (
          <button
            key={item.page}
            type="button"
            className={`nav-item ${
              currentPage === item.page ? 'active' : ''
            }`}
            onClick={() => onNavigate(item.page)}
            aria-current={
              currentPage === item.page ? 'page' : undefined
            }
          >
            <span className="nav-icon" aria-hidden="true">
              {item.icon}
            </span>

            {item.label}

            {item.page === 'tickets' && (
              <span className="nav-count">
                {totalTickets}
              </span>
            )}

            {item.page === 'ai' && (
              <span className="soon">BETA</span>
            )}
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="development-tag">
          ◉ AMBIENTE DE DESENVOLVIMENTO
        </div>

        <p>
          PulseOps AI
          <br />
          Dashboard operacional
        </p>
      </div>
    </aside>
  )
}
