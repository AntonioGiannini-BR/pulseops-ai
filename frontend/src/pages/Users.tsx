import { useEffect, useState, type FormEvent } from 'react'
import { createManagedUser, getManagedUsers, getTeamSummary, updateManagedUserStatus } from '../services/api'
import type { ManagedUser, UserCreatePayload, TeamSummary } from '../types/api'
import '../styles/operations.css'

const emptyForm: UserCreatePayload = {
  full_name: '',
  email: '',
  password: '',
  role: 'solicitante',
  department_id: null,
}

export default function Users({ token }: { token: string }) {
  const [users, setUsers] = useState<ManagedUser[]>([])
  const [teams, setTeams] = useState<TeamSummary[]>([])
  const [form, setForm] = useState<UserCreatePayload>(emptyForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [updatingId, setUpdatingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setError(null)
    setLoading(true)
    void Promise.all([
      getManagedUsers(token, controller.signal),
      getTeamSummary(token, controller.signal),
    ]).then(([members, departments]) => {
      if (!controller.signal.aborted) {
        setUsers(members)
        setTeams(departments)
      }
    }).catch((err: unknown) => {
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err.message : 'Não foi possível carregar as contas.')
      }
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false)
    })
    return () => controller.abort()
  }, [token])

  async function createAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    setError(null)
    setNotice(null)
    setSaving(true)
    try {
      const created = await createManagedUser(token, form)
      setUsers((current) => [created, ...current].slice(0, 100))
      setForm({ ...emptyForm })
      setNotice('Conta criada. Compartilhe a senha inicial somente por um canal seguro.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível criar a conta.')
    } finally {
      setSaving(false)
    }
  }

  async function changeStatus(user: ManagedUser) {
    if (updatingId !== null) return
    const action = user.is_active ? 'desativar' : 'reativar'
    if (!window.confirm('Confirmar ' + action + ' a conta ' + user.email + '?')) return
    setUpdatingId(user.id)
    setError(null)
    setNotice(null)
    try {
      const updated = await updateManagedUserStatus(token, user.id, !user.is_active)
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item))
      setNotice('Conta ' + (updated.is_active ? 'reativada' : 'desativada') + ' com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível alterar a conta.')
    } finally {
      setUpdatingId(null)
    }
  }

  return (
    <div className="operations-accounts">
      <section className="panel operations-panel" aria-labelledby="accounts-title">
        <div className="panel-top">
          <div>
            <h2 id="accounts-title">Administração de contas</h2>
            <p>Apenas administradores podem criar, desativar ou reativar contas.</p>
          </div>
          <span className="light-tag">{users.length} exibidas</span>
        </div>

        {notice && <p role="status" className="account-notice">{notice}</p>}
        {error && <p role="alert" className="operations-error">{error}</p>}

        <form className="account-form" onSubmit={(event) => void createAccount(event)}>
          <h3>Cadastrar novo usuário</h3>
          <div className="account-form-grid">
            <label>
              Nome completo
              <input required minLength={2} maxLength={150}
                value={form.full_name}
                onChange={(event) => setForm((prev) => ({ ...prev, full_name: event.target.value }))}
                disabled={saving} />
            </label>
            <label>
              E-mail
              <input required type="email" maxLength={255}
                value={form.email}
                onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
                disabled={saving} />
            </label>
            <label>
              Perfil
              <select value={form.role}
                onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value as UserCreatePayload['role'] }))}
                disabled={saving}>
                <option value="solicitante">Solicitante</option>
                <option value="analista">Analista</option>
              </select>
            </label>
            <label>
              Departamento
              <select value={form.department_id ?? ''}
                onChange={(event) => setForm((prev) => ({ ...prev, department_id: event.target.value ? Number(event.target.value) : null }))}
                disabled={saving}>
                <option value="">Sem departamento</option>
                {teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}
              </select>
            </label>
            <label>
              Senha inicial (mínimo 12 caracteres)
              <input required type="password" minLength={12} maxLength={128}
                autoComplete="new-password"
                value={form.password}
                onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
                disabled={saving} />
            </label>
          </div>
          <p className="operations-caption">A senha é armazenada somente como hash. Evite reutilizar senhas e não envie credenciais por e-mail público.</p>
          <button type="submit" className="account-primary" disabled={saving || loading}>
            {saving ? 'Criando conta...' : 'Criar conta'}
          </button>
        </form>
      </section>

      <section className="panel operations-panel" aria-label="Contas cadastradas">
        <h3>Contas cadastradas</h3>
        {loading && <p role="status">Carregando usuários...</p>}
        {!loading && !error && users.length === 0 && <p>Nenhuma conta encontrada.</p>}
        {!loading && users.length > 0 && (
          <div className="table-overflow">
            <table>
              <thead>
                <tr>
                  <th scope="col">Usuário</th><th scope="col">Perfil</th>
                  <th scope="col">Departamento</th><th scope="col">Situação</th>
                  <th scope="col">Ação</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td><strong>{user.full_name}</strong><div className="account-email">{user.email}</div></td>
                    <td>{user.role}</td>
                    <td>{teams.find((team) => team.id === user.department_id)?.name ?? '—'}</td>
                    <td>{user.is_active ? 'Ativa' : 'Inativa'}</td>
                    <td>
                      {user.role === 'admin' ? 'Conta protegida' : (
                        <button type="button" className="account-secondary"
                          disabled={updatingId !== null}
                          onClick={() => void changeStatus(user)}>
                          {updatingId === user.id ? 'Salvando...' : user.is_active ? 'Desativar' : 'Reativar'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="operations-caption">Exibindo as 100 contas mais recentes. Administradores não podem ser alterados por esta tela; para gestão corporativa, ainda será necessário integrar convites e SSO.</p>
      </section>
    </div>
  )
}
