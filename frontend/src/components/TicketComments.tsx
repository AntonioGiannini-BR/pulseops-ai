import { useEffect, useState } from 'react'
import { getTicketComments } from '../services/api'
import TicketCommentForm from './TicketCommentForm'
import type { TicketComment } from '../types/tickets'

import '../styles/ticket-comments.css'

interface TicketCommentsProps {
  token: string
  ticketId: number
}

function formatDate(value: string) {
  const date = new Date(value)

  return Number.isNaN(date.getTime())
    ? 'Data indisponível'
    : date.toLocaleString('pt-BR')
}

export default function TicketComments({
  token,
  ticketId,
}: TicketCommentsProps) {
  const [comments, setComments] = useState<TicketComment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    setLoading(true)
    setError(null)
    setComments([])

    async function loadComments() {
      try {
        const data = await getTicketComments(
          token,
          ticketId,
          controller.signal,
        )

        if (!controller.signal.aborted) {
          setComments(data)
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Não foi possível carregar os comentários.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadComments()

    return () => controller.abort()
  }, [token, ticketId])

  return (
    <section className="ticket-comments">
      <h3>Comentários ({comments.length})</h3>

      {loading && (
        <p role="status">Carregando comentários...</p>
      )}

      {error && (
        <p role="alert">{error}</p>
      )}

      {!loading && !error && comments.length === 0 && (
        <p>Nenhum comentário registrado.</p>
      )}

      {!loading && !error && comments.length > 0 && (
        <div className="ticket-comments-list">
          {comments.map((comment) => (
            <article
              key={comment.id}
              className="ticket-comment-card"
            >
              <div className="ticket-comment-header">
                <strong>
                  Usuário #{comment.author_id}
                </strong>

                <span
                  className={
                    comment.is_internal
                      ? 'ticket-comment-type internal'
                      : 'ticket-comment-type public'
                  }
                >
                  {comment.is_internal
                    ? 'Interno'
                    : 'Público'}
                </span>
              </div>

              <time dateTime={comment.created_at}>
                {formatDate(comment.created_at)}
              </time>

              <p>{comment.body}</p>
            </article>
          ))}
        </div>
      )}
      {!loading && !error && (
        <TicketCommentForm
          token={token}
          ticketId={ticketId}
          onCreated={(comment) =>
            setComments((current) => [...current, comment])
          }
        />
      )}
    </section>
  )
}
