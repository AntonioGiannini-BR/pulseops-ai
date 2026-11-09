import { useEffect, useState } from 'react'
import { updateTicketPriority } from '../services/api'
import type { TicketPriority } from '../types/tickets'

interface TicketPriorityControlProps {
  token: string
  ticketId: number
  priority: TicketPriority
  onUpdated: (priority: TicketPriority, dueAt: string | null) => void
}

export default function TicketPriorityControl({
  token,
  ticketId,
  priority,
  onUpdated,
}: TicketPriorityControlProps) {
  const [selected, setSelected] = useState<TicketPriority>(priority)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Uma sugestão de IA aprovada também pode alterar a prioridade.
  useEffect(() => {
    setSelected(priority)
  }, [priority])

  async function handleSave() {
    if (saving || selected === priority) return

    setSaving(true)
    setError(null)

    try {
      const updated = await updateTicketPriority(
        token,
        ticketId,
        selected,
      )

      onUpdated(updated.priority, updated.due_at)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Não foi possível alterar a prioridade.'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="ticket-status-action ticket-priority-action">
      <div>
        <strong>Prioridade do chamado</strong>
        <p>Selecione a nova prioridade e salve a alteração.</p>
      </div>

      <div className="ticket-priority-controls">
        <label htmlFor={`ticket-priority-${ticketId}`}>
          Nova prioridade
        </label>

        <select
          id={`ticket-priority-${ticketId}`}
          value={selected}
          disabled={saving}
          onChange={(event) => {
            setSelected(event.target.value as TicketPriority)
            setError(null)
          }}
        >
          <option value="baixa">Baixa</option>
          <option value="media">Média</option>
          <option value="alta">Alta</option>
          <option value="critica">Crítica</option>
        </select>

        <button
          type="button"
          disabled={saving || selected === priority}
          onClick={() => void handleSave()}
        >
          {saving ? 'Salvando...' : 'Salvar prioridade'}
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
