import { useEffect, useState } from 'react'
import { getTeamSummary } from '../services/api'
import type { TeamSummary } from '../types/api'
import '../styles/operations.css'

export default function Teams({ token }: { token: string }) {
  const [teams, setTeams] = useState<TeamSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    void getTeamSummary(token, controller.signal)
      .then((items) => { if (!controller.signal.aborted) setTeams(items) })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : 'Não foi possível consultar as equipes.')
        }
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [token])

  return (
    <section className="panel operations-panel" aria-label="Equipes e departamentos">
      <div className="panel-top">
        <div>
          <h2>Equipes e departamentos</h2>
          <p>Dados agregados de colaboradores ativos e chamados por área.</p>
        </div>
        <span className="light-tag">{teams.length} departamentos</span>
      </div>
      {loading && <p role="status">Carregando departamentos...</p>}
      {error && <p role="alert" className="operations-error">{error}</p>}
      {!loading && !error && teams.length === 0 && <p>Nenhum departamento cadastrado.</p>}
      {!loading && !error && teams.length > 0 && (
        <div className="table-overflow">
          <table>
            <thead>
              <tr>
                <th scope="col">Departamento</th>
                <th scope="col">Colaboradores ativos</th>
                <th scope="col">Analistas ativos</th>
                <th scope="col">Chamados</th>
                <th scope="col">Em aberto</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((team) => (
                <tr key={team.id}>
                  <td><strong>{team.name}</strong></td>
                  <td>{team.active_users}</td>
                  <td>{team.analysts}</td>
                  <td>{team.tickets_total}</td>
                  <td>{team.tickets_open}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="operations-caption">
        Os totais representam os departamentos associados aos registros; chamados sem departamento não entram nesta tabela.
        A base demonstrativa pode conter usuários fictícios inativos.
      </p>
    </section>
  )
}
