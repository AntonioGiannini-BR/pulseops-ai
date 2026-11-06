import { useEffect, useState } from 'react'
import { assignTicket, getAnalysts } from '../services/api'
import type { Analyst } from '../types/tickets'

interface TicketAssignmentControlProps {
  token: string
  ticketId: number
  assigneeId: number | null
  onAssigned: (assigneeId: number) => void
}

export default function TicketAssignmentControl({
  token,
  ticketId,
  assigneeId,
  onAssigned,
}: TicketAssignmentControlProps) {
  const [analysts, setAnalysts] = useState<Analyst[]>([])
  const [selectedId, setSelectedId] = useState(
    assigneeId === null ? '' : String(assigneeId)
  )
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    setLoading(true)
    setError(null)

    void getAnalysts(token, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setAnalysts(data)
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Não foi possível carregar os analistas.'
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      })

    return () => controller.abort()
  }, [token])

  useEffect(() => {
    setSelectedId(
      assigneeId === null ? '' : String(assigneeId)
    )
  }, [assigneeId, ticketId])

  async function handleAssign() {
    const id = Number(selectedId)

    if (
      saving ||
      !Number.isInteger(id) ||
      id <= 0 ||
      id === assigneeId
    ) {
      return
    }

    setSaving(true)
    setError(null)

    try {
      const updated = await assignTicket(token, ticketId, id)
      onAssigned(updated.assignee_id!)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Não foi possível atribuir o chamado.'
      )
    } finally {
      setSaving(false)
    }
  }

  const currentAnalyst = analysts.find(
    (analyst) => analyst.id === assigneeId
  )

  return (
    <div className="ticket-status-action ticket-priority-action">
      <div>
        <strong>Responsável pelo chamado</strong>
        <p>
          {assigneeId === null
            ? 'Nenhum analista atribuído.'
            : `Atual: ${currentAnalyst?.email ?? `Analista #${assigneeId}`}`}
        </p>
      </div>

      <div className="ticket-priority-controls">
        <label htmlFor={`ticket-assignee-${ticketId}`}>
          Analista
        </label>

        <select
          id={`ticket-assignee-${ticketId}`}
          value={selectedId}
          disabled={loading || saving}
          onChange={(event) => {
            setSelectedId(event.target.value)
            setError(null)
          }}
        >
          <option value="">
            {loading ? 'Carregando...' : 'Selecione um analista'}
          </option>

          {analysts.map((analyst) => (
            <option key={analyst.id} value={analyst.id}>
              {analyst.email}
            </option>
          ))}

          {assigneeId !== null && !currentAnalyst && (
            <option value={assigneeId}>
              Analista #{assigneeId} (indisponível)
            </option>
          )}
        </select>

        <button
          type="button"
          disabled={
            loading ||
            saving ||
            selectedId === '' ||
            Number(selectedId) === assigneeId
          }
          onClick={() => void handleAssign()}
        >
          {saving ? 'Atribuindo...' : 'Atribuir chamado'}
        </button>
      </div>

      {error && (
        <p className="ticket-status-error" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
