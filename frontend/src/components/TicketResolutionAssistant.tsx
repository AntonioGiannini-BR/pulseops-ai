import { useEffect, useState } from 'react'
import {
  executeResolutionAutomation,
  generateResolutionGuide,
  getResolutionAutomations,
} from '../services/api'
import type {
  ResolutionAutomationAction,
  ResolutionAutomationCatalog,
  ResolutionAutomationResult,
  ResolutionGuideResponse,
  TicketStatus,
} from '../types/tickets'
import '../styles/ticket-resolution.css'

interface Props {
  token: string
  ticketId: number
  ticketStatus: TicketStatus
  onExecuted: (result: ResolutionAutomationResult) => void
}

export default function TicketResolutionAssistant({
  token,
  ticketId,
  ticketStatus,
  onExecuted,
}: Props) {
  const [catalog, setCatalog] = useState<ResolutionAutomationCatalog | null>(null)
  const [guide, setGuide] = useState<ResolutionGuideResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [executing, setExecuting] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [diagnostic, setDiagnostic] = useState<ResolutionAutomationResult['diagnostic']>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    setCatalog(null)
    setGuide(null)
    setNotice(null)
    setDiagnostic(null)
    void getResolutionAutomations(token, ticketId, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setCatalog(data)
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : 'Falha ao carregar automações.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [token, ticketId, ticketStatus])

  async function handleGuide() {
    if (generating || executing || ticketStatus === 'resolvido' || ticketStatus === 'fechado') return
    setGenerating(true)
    setError(null)
    setGuide(null)
    try {
      setGuide(await generateResolutionGuide(token, ticketId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível gerar o plano.')
    } finally {
      setGenerating(false)
    }
  }

  async function handleExecute(action: ResolutionAutomationAction) {
    if (!catalog || !action.available || executing || generating) return
    // A confirmação é específica e exibe a ação antes de qualquer mutação.
    if (!window.confirm(
      `Aprovar a ação "${action.label}" no chamado #${ticketId}?\n\n${action.preview}\n\nEsta ação será registrada no histórico.`
    )) return

    setExecuting(action.id)
    setError(null)
    setNotice(null)
    setDiagnostic(null)
    try {
      const result = await executeResolutionAutomation(
        token, ticketId, action.id, catalog.expected_status
      )
      setNotice(result.message)
      setDiagnostic(result.diagnostic)
      onExecuted(result)
      setCatalog(await getResolutionAutomations(token, ticketId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao executar automação.')
      try {
        setCatalog(await getResolutionAutomations(token, ticketId))
      } catch {
        // O erro original continua visível.
      }
    } finally {
      setExecuting(null)
    }
  }

  const completed = ticketStatus === 'resolvido' || ticketStatus === 'fechado'

  return (
    <section className="ticket-resolution" aria-label="Assistente de resolução">
      <div className="ticket-resolution-heading">
        <div>
          <h3>Assistente de resolução</h3>
          <p>Gere um plano com IA e execute somente ações autorizadas por você.</p>
        </div>
        <button
          type="button"
          onClick={() => void handleGuide()}
          disabled={completed || generating || executing !== null}
        >
          {generating ? 'Preparando plano...' : 'Gerar plano com IA'}
        </button>
      </div>

      {guide && (
        <article className="ticket-resolution-guide">
          <p className="ticket-resolution-model">
            {guide.model_name.startsWith('demo-')
              ? 'Guia demonstrativo — não gerado por LLM'
              : `Plano sugerido por ${guide.model_name}`}
          </p>
          <h4>Hipótese inicial</h4>
          <p>{guide.guide.probable_cause}</p>
          <h4>Passos recomendados ao analista</h4>
          <ol>
            {guide.guide.steps.map((step, index) => <li key={index}>{step}</li>)}
          </ol>
          <h4>Como verificar a solução</h4>
          <p>{guide.guide.verification}</p>
          <h4>Resposta sugerida ao solicitante</h4>
          <p className="ticket-resolution-draft">{guide.guide.requester_reply}</p>
          <p className="ticket-resolution-disclaimer">
            O plano é uma sugestão, não um diagnóstico confirmado. A IA não executou esses passos.
          </p>
        </article>
      )}

      <h4 className="ticket-resolution-subtitle">Automações disponíveis</h4>
      <p className="ticket-resolution-disclaimer">
        Ações controladas pelo backend, independentes do texto gerado pela IA.
        Cada execução exige confirmação e é auditada. Nenhuma ação acessa portais externos.
      </p>

      {loading && <p role="status">Carregando automações...</p>}
      {error && <p className="ticket-resolution-error" role="alert">{error}</p>}
      {notice && <p className="ticket-resolution-success" role="status">{notice}</p>}
      {diagnostic && (
        <p className="ticket-resolution-success">
          API: {diagnostic.api} · PostgreSQL: {diagnostic.database}
        </p>
      )}

      {catalog && (
        <div className="ticket-resolution-actions">
          {catalog.actions.map((action) => (
            <article className="ticket-resolution-action" key={action.id}>
              <div>
                <h5>{action.label}</h5>
                <p>{action.description}</p>
                <pre>{action.preview}</pre>
                {!action.available && <small>{action.reason}</small>}
              </div>
              <button
                type="button"
                onClick={() => void handleExecute(action)}
                disabled={!action.available || executing !== null || generating}
              >
                {executing === action.id ? 'Executando...' : 'Revisar e executar'}
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
