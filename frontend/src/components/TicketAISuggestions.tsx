import { useEffect, useState } from 'react'
import {
  generateTicketAISuggestion,
  getAIProviderStatus,
  getCategories,
  getTicketAISuggestions,
  reviewTicketAISuggestion,
} from '../services/api'
import type {
  Category,
  AIProviderStatus,
  TicketAISuggestion,
  TicketAIReviewResult,
  TicketPriority,
  TicketStatus,
} from '../types/tickets'
import '../styles/ticket-ai.css'

interface Props {
  token: string
  ticketId: number
  ticketStatus: TicketStatus
  onReviewed: (result: TicketAIReviewResult) => void
  onCreated: () => void
}

const priorityLabels: Record<TicketPriority, string> = {
  baixa: 'Baixa',
  media: 'Média',
  alta: 'Alta',
  critica: 'Crítica',
}

const reviewLabels = {
  pendente: 'Aguardando revisão',
  aprovada: 'Aprovada',
  rejeitada: 'Rejeitada',
}

export default function TicketAISuggestions({
  token,
  ticketId,
  ticketStatus,
  onReviewed,
  onCreated,
}: Props) {
  const [suggestions, setSuggestions] = useState<TicketAISuggestion[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [providerStatus, setProviderStatus] = useState<AIProviderStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [reviewingId, setReviewingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    setNotice(null)
    setSuggestions([])
    setProviderStatus(null)

    void Promise.all([
      getTicketAISuggestions(token, ticketId, controller.signal),
      getCategories(token, controller.signal),
      getAIProviderStatus(token, controller.signal),
    ]).then(([items, activeCategories, status]) => {
      if (!controller.signal.aborted) {
        setSuggestions(items)
        setCategories(activeCategories)
        setProviderStatus(status)
      }
    }).catch((err: unknown) => {
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err.message : 'Falha ao carregar sugestões.')
      }
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false)
    })

    return () => controller.abort()
  }, [token, ticketId])

  const pending = suggestions.some((item) => item.review_status === 'pendente')
  const completed = ticketStatus === 'resolvido' || ticketStatus === 'fechado'
  const busy = generating || reviewingId !== null
  const providerUnconfigured = providerStatus?.provider === 'openai' && !providerStatus.configured

  function categoryLabel(id: number | null) {
    if (id === null) return 'Não sugerida'
    return categories.find((item) => item.id === id)?.name ?? `Categoria #${id}`
  }

  async function handleGenerate() {
    if (loading || pending || completed || busy || providerUnconfigured) return
    setGenerating(true)
    setError(null)
    setNotice(null)
    try {
      const suggestion = await generateTicketAISuggestion(token, ticketId)
      setSuggestions((items) => [suggestion, ...items])
      setNotice('Sugestão criada. Nenhuma alteração foi aplicada ao chamado.')
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível gerar sugestão.')
    } finally {
      setGenerating(false)
    }
  }

  async function handleReview(suggestionId: number, decision: 'aprovada' | 'rejeitada') {
    if (busy) return
    setReviewingId(suggestionId)
    setError(null)
    setNotice(null)
    try {
      const result = await reviewTicketAISuggestion(token, ticketId, suggestionId, decision)
      setSuggestions((items) =>
        items.map((item) => item.id === suggestionId ? result.suggestion : item)
      )
      onReviewed(result)
      setNotice(
        decision === 'aprovada'
          ? 'Sugestão aprovada. Prioridade e categoria atualizadas.'
          : 'Sugestão rejeitada. O chamado não foi alterado.'
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível revisar sugestão.')
    } finally {
      setReviewingId(null)
    }
  }

  return (
    <section className="ticket-ai">
      <div className="ticket-ai-heading">
        <div>
          <h3>Triagem assistida</h3>
          <p>As sugestões só alteram o chamado depois da sua aprovação.</p>
        </div>
        <button
          type="button"
          disabled={loading || pending || completed || busy || providerUnconfigured}
          onClick={() => void handleGenerate()}
        >
          {generating ? 'Analisando...' : 'Gerar sugestão'}
        </button>
      </div>

      {providerStatus && (
        <p className="ticket-ai-hint" role="status">
          {providerStatus.provider === 'mock'
            ? 'Modo demonstração: regras locais, sem modelo de IA.'
            : providerStatus.configured
              ? `Modelo externo configurado (${providerStatus.model}). Ao gerar, parte do chamado será enviada ao provedor.`
              : 'IA externa sem chave configurada no backend. Configure OPENAI_API_KEY para gerar sugestões.'}
        </p>
      )}
      {completed && <p className="ticket-ai-hint">Chamados concluídos não recebem novas sugestões.</p>}
      {pending && <p className="ticket-ai-hint">Revise a sugestão pendente para gerar outra.</p>}
      {loading && <p role="status">Carregando sugestões...</p>}
      {error && <p role="alert" className="ticket-ai-error">{error}</p>}
      {notice && <p role="status" className="ticket-ai-notice">{notice}</p>}

      {!loading && suggestions.length === 0 && (
        <p className="ticket-ai-hint">Nenhuma sugestão registrada para este chamado.</p>
      )}

      {!loading && suggestions.map((suggestion) => (
        <article className="ticket-ai-card" key={suggestion.id}>
          <div className="ticket-ai-card-head">
            <strong>Sugestão #{suggestion.id}</strong>
            <span className={`ticket-ai-status ${suggestion.review_status}`}>
              {reviewLabels[suggestion.review_status]}
            </span>
          </div>

          <p className="ticket-ai-summary">{suggestion.summary ?? 'Sem resumo'}</p>
          <dl className="ticket-ai-fields">
            <div>
              <dt>Prioridade sugerida</dt>
              <dd>
                {suggestion.suggested_priority
                  ? priorityLabels[suggestion.suggested_priority]
                  : 'Não sugerida'}
              </dd>
            </div>
            <div>
              <dt>Categoria sugerida</dt>
              <dd>{categoryLabel(suggestion.suggested_category_id)}</dd>
            </div>
          </dl>
          {suggestion.rationale && <p className="ticket-ai-rationale">{suggestion.rationale}</p>}
          <p className="ticket-ai-origin">
            {suggestion.model_name?.startsWith('demo-')
              ? 'Modo demonstração — regras locais, sem modelo de IA'
              : `Modelo: ${suggestion.model_name ?? 'não informado'}`}
          </p>

          {suggestion.review_status === 'pendente' && (
            <div className="ticket-ai-actions">
              <button
                type="button"
                disabled={busy || completed}
                onClick={() => void handleReview(suggestion.id, 'aprovada')}
              >
                {reviewingId === suggestion.id ? 'Salvando...' : 'Aprovar e aplicar'}
              </button>
              <button
                type="button"
                className="ticket-ai-reject"
                disabled={busy}
                onClick={() => void handleReview(suggestion.id, 'rejeitada')}
              >
                Rejeitar
              </button>
            </div>
          )}
          {suggestion.reviewed_at && (
            <small className="ticket-ai-reviewed">
              Revisada em {new Date(suggestion.reviewed_at).toLocaleString('pt-BR')}
              {suggestion.reviewed_by_id !== null && ` por usuário #${suggestion.reviewed_by_id}`}
            </small>
          )}
        </article>
      ))}
    </section>
  )
}
