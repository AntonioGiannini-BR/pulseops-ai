import { useEffect, useState } from 'react'
import { getTicketHistory } from '../services/api'
import type { TicketHistoryEvent } from '../types/tickets'

import '../styles/ticket-history.css'

interface TicketHistoryProps {
  token: string
  ticketId: number
}

const actionLabels: Record<string, string> = {
  criacao: 'Chamado criado',
  mudanca_status: 'Status atualizado',
  mudanca_prioridade: 'Prioridade alterada',
  atribuicao: 'Analista atribuído',
  mudanca_categoria: 'Categoria alterada',
  ai_sugestao_criada: 'Sugestão de triagem criada',
  ai_sugestao_aprovada: 'Sugestão de triagem aprovada',
  ai_sugestao_rejeitada: 'Sugestão de triagem rejeitada',
}

const valueLabels: Record<string, string> = {
  aberto: 'Aberto',
  em_triagem: 'Em triagem',
  em_atendimento: 'Em atendimento',
  resolvido: 'Resolvido',
  fechado: 'Fechado',
  baixa: 'Baixa',
  media: 'Média',
  alta: 'Alta',
  critica: 'Crítica',
}

function formatValue(value: string | null) {
  if (value === null) return 'Não informado'
  return valueLabels[value] ?? value
}

function formatDate(value: string) {
  const date = new Date(value)

  return Number.isNaN(date.getTime())
    ? 'Data indisponível'
    : date.toLocaleString('pt-BR')
}

export default function TicketHistory({
  token,
  ticketId,
}: TicketHistoryProps) {
  const [events, setEvents] = useState<TicketHistoryEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    setLoading(true)
    setError(null)
    setEvents([])

    async function loadHistory() {
      try {
        const data = await getTicketHistory(
          token,
          ticketId,
          controller.signal,
        )

        if (!controller.signal.aborted) {
          setEvents(data)
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Não foi possível carregar o histórico.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadHistory()

    return () => controller.abort()
  }, [token, ticketId])

  return (
    <section className="ticket-history">
      <h3>Histórico de alterações</h3>

      {loading && (
        <p role="status">Carregando histórico...</p>
      )}

      {error && (
        <p role="alert">{error}</p>
      )}

      {!loading && !error && events.length === 0 && (
        <p>Nenhuma movimentação registrada.</p>
      )}

      {!loading && !error && events.length > 0 && (
        <ol className="ticket-timeline">
          {events.map((event) => (
            <li key={event.id} className="ticket-timeline-item">
              <span
                className="ticket-timeline-dot"
                aria-hidden="true"
              />

              <div className="ticket-timeline-content">
                <strong>
                  {actionLabels[event.action] ?? event.action}
                </strong>

                <time dateTime={event.created_at}>
                  {formatDate(event.created_at)}
                </time>

                {(event.old_value !== null ||
                  event.new_value !== null) && (
                  <p>
                    {formatValue(event.old_value)}
                    {' → '}
                    {formatValue(event.new_value)}
                  </p>
                )}

                <small>
                  {event.actor_id !== null
                    ? `Realizado pelo usuário #${event.actor_id}`
                    : 'Responsável não identificado'}
                </small>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
