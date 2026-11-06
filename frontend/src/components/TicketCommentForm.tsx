import { useState } from 'react'
import type { FormEvent } from 'react'
import { createTicketComment } from '../services/api'
import type { TicketComment } from '../types/tickets'

import '../styles/ticket-comment-form.css'

interface TicketCommentFormProps {
  token: string
  ticketId: number
  onCreated: (comment: TicketComment) => void
}

export default function TicketCommentForm({
  token,
  ticketId,
  onCreated,
}: TicketCommentFormProps) {
  const [body, setBody] = useState('')
  const [isInternal, setIsInternal] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (saving) return

    const text = body.trim()

    if (!text) {
      setError('Digite um comentário antes de publicar.')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const comment = await createTicketComment(
        token,
        ticketId,
        {
          body: text,
          is_internal: isInternal,
        },
      )

      onCreated(comment)
      setBody('')
      setIsInternal(false)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Não foi possível publicar o comentário.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="ticket-comment-form"
      onSubmit={handleSubmit}
    >
      <h4>Adicionar comentário</h4>

      <label htmlFor={`comment-body-${ticketId}`}>
        Mensagem
      </label>

      <textarea
        id={`comment-body-${ticketId}`}
        placeholder="Descreva a atualização do atendimento..."
        value={body}
        onChange={(event) => setBody(event.target.value)}
        maxLength={5000}
        rows={4}
        required
        disabled={saving}
      />

      <label className="ticket-comment-checkbox">
        <input
          type="checkbox"
          checked={isInternal}
          onChange={(event) =>
            setIsInternal(event.target.checked)
          }
          disabled={saving}
        />
        <span>Comentário interno (somente equipe autorizada)</span>
      </label>

      {error && (
        <p className="ticket-comment-error" role="alert">
          {error}
        </p>
      )}

      <div className="ticket-comment-form-footer">
        <span>{body.length}/5000 caracteres</span>

        <button
          type="submit"
          disabled={saving || !body.trim()}
        >
          {saving ? 'Publicando...' : 'Publicar comentário'}
        </button>
      </div>
    </form>
  )
}
