import { useEffect, useState } from 'react'

import KpiCard from '../components/KpiCard'
import StatusChart from '../components/StatusChart'
import PriorityChart from '../components/PriorityChart'

import { getDashboardDistribution } from '../services/api'

import type {
  DashboardSummary,
  DashboardDistribution,
} from '../types/api'

import '../styles/charts.css'

const REFRESH_INTERVAL_MS = 30_000

interface DashboardProps {
  summary: DashboardSummary | null
  loading: boolean
  token: string
}

export default function Dashboard({
  summary,
  loading,
  token,
}: DashboardProps) {
  const [distribution, setDistribution] =
    useState<DashboardDistribution | null>(null)

  const [chartsLoading, setChartsLoading] = useState(true)
  const [chartsError, setChartsError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    let timeoutId: ReturnType<typeof setTimeout> | undefined

    setChartsLoading(true)
    setChartsError(null)
    setDistribution(null)

    async function carregarGraficos() {
      try {
        const dados = await getDashboardDistribution(
          token,
          controller.signal,
        )

        if (!controller.signal.aborted) {
          setDistribution(dados)
          setChartsError(null)
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setChartsError(
            err instanceof Error
              ? err.message
              : 'Não foi possível carregar os gráficos.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setChartsLoading(false)

          timeoutId = setTimeout(() => {
            void carregarGraficos()
          }, REFRESH_INTERVAL_MS)
        }
      }
    }

    void carregarGraficos()

    return () => {
      controller.abort()

      if (timeoutId !== undefined) {
        clearTimeout(timeoutId)
      }
    }
  }, [token])

  function formatarValor(numero?: number) {
    if (loading || numero === undefined) {
      return '—'
    }

    return numero.toLocaleString('pt-BR')
  }

  function formatarHoras(numero?: number | null) {
    if (loading || numero == null) {
      return '—'
    }

    return numero.toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  }

  return (
    <>
      <div className="kpi-grid">
        <KpiCard
          title="Total de chamados"
          value={formatarValor(summary?.total_chamados)}
          description="Registrados na operação"
          icon="▦"
          color="blue"
        />

        <KpiCard
          title="Em andamento"
          value={formatarValor(summary?.chamados_pendentes)}
          description="Aguardando resolução"
          icon="◷"
          color="purple"
        />

        <KpiCard
          title="Concluídos"
          value={formatarValor(summary?.chamados_concluidos)}
          description="Resolvidos ou fechados"
          icon="✓"
          color="green"
        />

        <KpiCard
          title="Fora do SLA"
          value={formatarValor(summary?.chamados_fora_sla)}
          description="Ocorrências com atraso"
          icon="⚑"
          color="orange"
        />
      </div>

      <section className="dashboard-analytics">
        <div className="analytics-heading">
          <div>
            <h2>Dashboard operacional</h2>
            <p>
              Distribuição dos chamados e desempenho da operação.
            </p>
          </div>

          <span className="analytics-badge">
            Atualização a cada 30 s
          </span>
        </div>

        {chartsError && (
          <div className="charts-error" role="alert">
            Erro ao carregar gráficos: {chartsError}
          </div>
        )}

        {chartsLoading && (
          <p className="charts-loading">
            Carregando gráficos...
          </p>
        )}

        {distribution && (
          <div className="charts-grid">
            <StatusChart distribution={distribution} />
            <PriorityChart distribution={distribution} />
          </div>
        )}

        <div className="resolution-card">
          <div>
            <span className="resolution-label">
              Tempo médio de resolução
            </span>

            <p>
              Média de horas necessárias para resolver chamados.
            </p>
          </div>

          <div className="resolution-value">
            {formatarHoras(summary?.horas_medias_resolucao)}
            <span> horas</span>
          </div>
        </div>
      </section>
    </>
  )
}
