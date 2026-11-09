import { useEffect, useRef, useState } from 'react'
import { getTicket, getCurrentUser, updateTicketStatus } from '../services/api'
import TicketHistory from './TicketHistory'
import TicketComments from './TicketComments'
import TicketPriorityControl from './TicketPriorityControl'
import TicketAssignmentControl from './TicketAssignmentControl'
import type {
  Ticket,
  TicketPriority,
  TicketStatus,
  TicketSlaStatus,
} from '../types/tickets'

import '../styles/ticket-details.css'
import '../styles/ticket-status.css'

interface TicketDetailsProps {
  token: string
  ticketId: number
  onClose: () => void
  onStatusChanged: (ticketId: number, status: TicketStatus) => void
  onPriorityChanged: (ticketId: number, priority: TicketPriority) => void
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

const slaLabels: Record<TicketSlaStatus, string> = {
  sem_prazo: 'Sem prazo definido',
  em_dia: 'Em dia',
  atrasado: 'Atrasado',
  dentro_do_prazo: 'Resolvido no prazo',
  fora_do_prazo: 'Resolvido fora do prazo',
}

function calcularSla(ticket: Ticket): TicketSlaStatus {
  if (!ticket.due_at) return 'sem_prazo'

  const prazo = new Date(ticket.due_at).getTime()
  if (Number.isNaN(prazo)) return 'sem_prazo'

  if (ticket.resolved_at) {
    const resolucao = new Date(ticket.resolved_at).getTime()
    return resolucao > prazo ? 'fora_do_prazo' : 'dentro_do_prazo'
  }

  return Date.now() > prazo ? 'atrasado' : 'em_dia'
}

const nextStatus: Record<TicketStatus, TicketStatus | null> = {
  aberto: 'em_triagem',
  em_triagem: 'em_atendimento',
  em_atendimento: 'resolvido',
  resolvido: 'fechado',
  fechado: null,
}

const actionLabels: Record<TicketStatus, string> = {
  aberto: 'Iniciar triagem',
  em_triagem: 'Iniciar atendimento',
  em_atendimento: 'Marcar como resolvido',
  resolvido: 'Fechar chamado',
  fechado: 'Concluído',
}

export default function TicketDetails({
  token,
  ticketId,
  onClose,
  onStatusChanged,
  onPriorityChanged,
}: TicketDetailsProps) {
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const [canUpdateStatus, setCanUpdateStatus] = useState(false)
  const [canAssignTickets, setCanAssignTickets] = useState(false)
  const [statusSaving, setStatusSaving] = useState(false)
  const [historyRevision, setHistoryRevision] = useState(0)
  const [statusError, setStatusError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadDetails() {
      setLoading(true)
      setError(null)
      setTicket(null)

      try {
        const data = await getTicket(
          token,
          ticketId,
          controller.signal,
        )

        if (!controller.signal.aborted) {
          setTicket(data)
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Não foi possível carregar o chamado.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadDetails()

    return () => controller.abort()
  }, [token, ticketId])

  useEffect(() => {
    const previousFocus =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null

    closeButtonRef.current?.focus()

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      previousFocus?.focus()
    }
  }, [onClose])

  useEffect(() => {
    const controller = new AbortController()

    void getCurrentUser(token, controller.signal)
      .then((user) => {
        if (!controller.signal.aborted) {
          setCanUpdateStatus(
            user.role === 'admin' || user.role === 'analista'
          )
          setCanAssignTickets(user.role === 'admin')
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setCanUpdateStatus(false)
          setCanAssignTickets(false)
        }
      })

    return () => controller.abort()
  }, [token])

  async function handleAdvanceStatus() {
    if (!ticket || !canUpdateStatus || statusSaving) return

    const next = nextStatus[ticket.status]
    if (!next) return

    setStatusSaving(true)
    setStatusError(null)

    try {
      const updated = await updateTicketStatus(
        token,
        ticketId,
        next,
      )

      setTicket((current) =>
        current
          ? {
              ...current,
              status: updated.status,
              resolved_at: updated.resolved_at,
              sla_status: undefined,
            }
          : current
      )

      onStatusChanged(ticketId, updated.status)
    } catch (err) {
      setStatusError(
        err instanceof Error
          ? err.message
          : 'Não foi possível atualizar o status.'
      )
    } finally {
      setStatusSaving(false)
    }
  }

  function formatDate(value: string) {
    const date = new Date(value)

    return Number.isNaN(date.getTime())
      ? '—'
      : date.toLocaleString('pt-BR')
  }

  return (
    <div
      className="modal-backdrop visible"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
    >
      <section
        className="modal ticket-details-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-details-title"
      >
        <div className="modal-header">
          <div>
            <span className="eyebrow">
              CHAMADO #{ticketId}
            </span>

            <h2 id="ticket-details-title">
              {ticket?.title ?? 'Detalhes do chamado'}
            </h2>
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            className="close-button"
            onClick={onClose}
            aria-label="Fechar detalhes"
          >
            ✕
          </button>
        </div>

        {loading && (
          <p role="status">Carregando detalhes...</p>
        )}

        {error && (
          <p role="alert">{error}</p>
        )}

        {ticket && (
          <>
            <div className="ticket-detail-summary">
              <div>
                <dt>Prioridade</dt>
                <dd>
                  <span className={`pill p-${ticket.priority}`}>
                    {priorityLabels[ticket.priority]}
                  </span>
                </dd>
              </div>

              <div>
                <dt>Status</dt>
                <dd>
                  <span className={`pill s-${ticket.status}`}>
                    {statusLabels[ticket.status]}
                  </span>
                </dd>
              </div>

              <div>
                <dt>Solicitante</dt>
                <dd>Usuário #{ticket.requester_id}</dd>
              </div>

              <div>
                <dt>Categoria</dt>
                <dd>Categoria #{ticket.category_id}</dd>
              </div>

              <div>
                <dt>Data de abertura</dt>
                <dd>{formatDate(ticket.opened_at)}</dd>
              </div>

              <div>
                <dt>Prazo de SLA</dt>
                <dd>{ticket.due_at ? formatDate(ticket.due_at) : 'Não definido'}</dd>
              </div>

              <div>
                <dt>Situação do SLA</dt>
                <dd>{slaLabels[calcularSla(ticket)]}</dd>
              </div>
            </div>

            {canUpdateStatus && nextStatus[ticket.status] !== null && (
              <div className="ticket-status-action">
                <div>
                  <strong>Fluxo de atendimento</strong>
                  <p>Avance para a próxima etapa do chamado.</p>
                </div>

                <button
                  type="button"
                  onClick={() => void handleAdvanceStatus()}
                  disabled={statusSaving}
                >
                  {statusSaving
                    ? 'Atualizando...'
                    : actionLabels[ticket.status]}
                </button>
              </div>
            )}

            {statusError && (
              <p className="ticket-status-error" role="alert">
                {statusError}
              </p>
            )}

            {canUpdateStatus && (
              <TicketPriorityControl
                token={token}
                ticketId={ticketId}
                priority={ticket.priority}
                onUpdated={(priority, dueAt) => {
                  setTicket((current) =>
                    current
                      ? {
                          ...current,
                          priority,
                          due_at: dueAt,
                          sla_status: undefined,
                        }
                      : current
                  )
                  onPriorityChanged(ticketId, priority)
                  setHistoryRevision((current) => current + 1)
                }}
              />
            )}

            {canAssignTickets && (
              <TicketAssignmentControl
                token={token}
                ticketId={ticketId}
                assigneeId={ticket.assignee_id}
                onAssigned={(assigneeId) => {
                  setTicket((current) =>
                    current
                      ? { ...current, assignee_id: assigneeId }
                      : current
                  )
                  setHistoryRevision((current) => current + 1)
                }}
              />
            )}

            <div className="ticket-detail-description">
              <h3>Descrição do chamado</h3>
              <p>{ticket.description}</p>
            </div>

            <TicketHistory
              key={`${ticketId}-${ticket.status}-${historyRevision}`}
              token={token}
              ticketId={ticketId}
            />

            <TicketComments
              token={token}
              ticketId={ticketId}
            />
          </>
        )}
      </section>
    </div>
  )
}
