import { useEffect, useState } from 'react'
import { getTickets } from '../services/api'
import { csvContent } from '../utils/csv'
import TicketDetails from '../components/TicketDetails'
import NewTicketModal from '../components/NewTicketModal'
import '../styles/tickets-actions.css'
import type {
  Ticket,
  TicketPriority,
  TicketStatus,
} from '../types/tickets'

interface TicketsProps {
  token: string
}

const statusLabels: Record<TicketStatus, string> = {
  aberto: 'Aberto',
  em_triagem: 'Em triagem',
  em_atendimento: 'Em atendimento',
  resolvido: 'Resolvido',
  fechado: 'Fechado',
}

const priorityLabels: Record<TicketPriority, string> = {
  baixa: 'Baixa',
  media: 'Média',
  alta: 'Alta',
  critica: 'Crítica',
}

export default function Tickets({ token }: TicketsProps) {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [isNewTicketOpen, setIsNewTicketOpen] = useState(false)
  const [selectedTicketId, setSelectedTicketId] =
    useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] =
    useState<TicketStatus | 'todos'>('todos')
  const [priorityFilter, setPriorityFilter] =
    useState<TicketPriority | 'todas'>('todas')

  useEffect(() => {
    const controller = new AbortController()

    async function loadTickets() {
      try {
        setLoading(true)
        setError(null)

        const data = await getTickets(token, controller.signal)

        if (!controller.signal.aborted) {
          setTickets(data)
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Erro ao carregar chamados.'
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadTickets()

    return () => controller.abort()
  }, [token])

  function formatDate(value: string) {
    const date = new Date(value)

    return Number.isNaN(date.getTime())
      ? '—'
      : date.toLocaleDateString('pt-BR')
  }

  const filteredTickets = tickets.filter((ticket) => {
    const query = search.trim().toLowerCase().replace(/^#/, '')

    const matchesSearch =
      ticket.title.toLowerCase().includes(query) ||
      String(ticket.id).includes(query)

    const matchesStatus =
      statusFilter === 'todos' ||
      ticket.status === statusFilter

    const matchesPriority =
      priorityFilter === 'todas' ||
      ticket.priority === priorityFilter

    return matchesSearch && matchesStatus && matchesPriority
  })

  function exportFilteredCsv() {
    if (filteredTickets.length === 0) return
    const content = csvContent(
      ['ID', 'Título', 'Prioridade', 'Status', 'Abertura'],
      filteredTickets.map((ticket) => [
        ticket.id,
        ticket.title,
        priorityLabels[ticket.priority],
        statusLabels[ticket.status],
        formatDate(ticket.opened_at),
      ]),
    )
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `pulseops-chamados-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
  }

  return (
    <>
    <section className="panel table-panel">
      <div className="panel-top">
        <div>
          <h2>Lista de chamados</h2>
          <p>Solicitações registradas na operação.</p>
        </div>

        <div className="tickets-panel-actions">
          <span className="light-tag">
            {filteredTickets.length} de {tickets.length} chamados
          </span>

          <button
            type="button"
            className="csv-export-trigger"
            onClick={exportFilteredCsv}
            disabled={loading || error !== null || filteredTickets.length === 0}
          >
            Exportar CSV
          </button>
          <button
            type="button"
            className="new-ticket-trigger"
            onClick={() => setIsNewTicketOpen(true)}
          >
            + Novo chamado
          </button>
        </div>
      </div>

      <div className="filters">
        <input
          type="search"
          placeholder="Buscar por título ou ID..."
          aria-label="Buscar chamados"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        <select
          aria-label="Filtrar por status"
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(event.target.value as TicketStatus | 'todos')
          }
        >
          <option value="todos">Todos os status</option>
          <option value="aberto">Aberto</option>
          <option value="em_triagem">Em triagem</option>
          <option value="em_atendimento">Em atendimento</option>
          <option value="resolvido">Resolvido</option>
          <option value="fechado">Fechado</option>
        </select>

        <select
          aria-label="Filtrar por prioridade"
          value={priorityFilter}
          onChange={(event) =>
            setPriorityFilter(event.target.value as TicketPriority | 'todas')
          }
        >
          <option value="todas">Todas as prioridades</option>
          <option value="baixa">Baixa</option>
          <option value="media">Média</option>
          <option value="alta">Alta</option>
          <option value="critica">Crítica</option>
        </select>
      </div>

      {loading && (
        <p className="table-message" role="status">
          Carregando chamados...
        </p>
      )}

      {error && (
        <p className="table-message" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && filteredTickets.length === 0 && (
        <p className="table-message">
          {tickets.length === 0
            ? 'Nenhum chamado cadastrado.'
            : 'Nenhum chamado corresponde aos filtros.'}
        </p>
      )}

      {!loading && !error && filteredTickets.length > 0 && (
        <div className="table-overflow">
          <table>
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">Título</th>
                <th scope="col">Prioridade</th>
                <th scope="col">Status</th>
                <th scope="col">Abertura</th>
              </tr>
            </thead>

            <tbody>
              {filteredTickets.map((ticket) => (
                <tr
                  key={ticket.id}
                  className="ticket-clickable-row"
                  onClick={() => setSelectedTicketId(ticket.id)}
                >
                  <td className="ticket-id">
                    <button
                      type="button"
                      className="ticket-open-button"
                      aria-label={`Abrir chamado ${ticket.id}`}
                      onClick={() => setSelectedTicketId(ticket.id)}
                    >
                      #{ticket.id}
                    </button>
                  </td>

                  <td className="ticket-title">
                    {ticket.title}
                  </td>

                  <td>
                    <span className={`pill p-${ticket.priority}`}>
                      {priorityLabels[ticket.priority]}
                    </span>
                  </td>

                  <td>
                    <span className={`pill s-${ticket.status}`}>
                      {statusLabels[ticket.status]}
                    </span>
                  </td>

                  <td>
                    {formatDate(ticket.opened_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>

    {selectedTicketId !== null && (
      <TicketDetails
        token={token}
        ticketId={selectedTicketId}
        onClose={() => setSelectedTicketId(null)}
        onPriorityChanged={(ticketId, priority) => {
          setTickets((current) =>
            current.map((item) =>
              item.id === ticketId
                ? { ...item, priority }
                : item
            )
          )
        }}
        onStatusChanged={(ticketId, status) => {
          setTickets((current) =>
            current.map((item) =>
              item.id === ticketId
                ? { ...item, status }
                : item
            )
          )
        }}
      />
    )}
    {isNewTicketOpen && (
      <NewTicketModal
        token={token}
        onClose={() => setIsNewTicketOpen(false)}
        onCreated={(ticket) => {
          setTickets((current) =>
            [...current, ticket].sort((a, b) => a.id - b.id)
          )
          setSearch('')
          setStatusFilter('todos')
          setPriorityFilter('todas')
          setIsNewTicketOpen(false)
        }}
      />
    )}
    </>
  )
}
