import { useEffect, useState } from 'react'
import { getAIOverview, getAIProviderStatus } from '../services/api'
import type { AIOverview } from '../types/api'
import type { AIProviderStatus } from '../types/tickets'
import '../styles/operations.css'

export default function AICenter({ token }: { token: string }) {
  const [overview, setOverview] = useState<AIOverview | null>(null)
  const [provider, setProvider] = useState<AIProviderStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    void Promise.all([
      getAIOverview(token, controller.signal),
      getAIProviderStatus(token, controller.signal),
    ])
      .then(([items, status]) => {
        if (!controller.signal.aborted) { setOverview(items); setProvider(status) }
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : 'Não foi possível consultar os indicadores de IA.')
        }
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [token])

  const providerName = provider?.provider === 'ollama'
    ? 'Ollama — IA local'
    : provider?.provider === 'openai'
      ? 'OpenAI — API externa'
      : 'Demonstração — regras locais'

  return (
    <section className="panel operations-panel" aria-label="Central de inteligência artificial">
      <div className="panel-top">
        <div>
          <h2>Central de IA</h2>
          <p>Visão geral da triagem supervisionada e do modelo selecionado.</p>
        </div>
      </div>
      {loading && <p role="status">Carregando estatísticas da IA...</p>}
      {error && <p role="alert" className="operations-error">{error}</p>}
      {!loading && !error && overview && provider && (
        <>
          <div className="operations-provider">
            <strong>{providerName}</strong>
            <p>Modelo: {provider.model ?? 'Sem LLM'}</p>
            <p>
              {provider.provider === 'mock'
                ? 'As regras demonstrativas não são um modelo de IA.'
                : provider.provider === 'ollama'
                  ? 'O modelo é processado localmente. Confirme que o Ollama está ativo.'
                  : provider.configured
                    ? 'A chave foi configurada no servidor; conectividade e créditos não são verificados aqui.'
                    : 'A chave externa ainda não foi configurada no servidor.'}
            </p>
          </div>
          <div className="operations-stats">
            {([
              ['Total de sugestões', overview.suggestions_total],
              ['Aguardando revisão', overview.pending],
              ['Aprovadas', overview.approved],
              ['Rejeitadas', overview.rejected],
              ['Geradas pelo Ollama', overview.ollama],
              ['Modo demonstração', overview.demonstration],
            ] as const).map(([label, value]) => (
              <div className="operations-stat" key={label}>
                <strong>{value}</strong><span>{label}</span>
              </div>
            ))}
          </div>
          <p className="operations-caption">
            Para gerar um plano ou executar uma automação, abra um chamado na página Chamados.
            Nenhum modelo tem permissão para executar comandos arbitrários.
            {overview.external_models > 0 && ` Sugestões de outros modelos: ${overview.external_models}.`}
          </p>
        </>
      )}
    </section>
  )
}
