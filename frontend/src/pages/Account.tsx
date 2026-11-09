import { useEffect, useState, type FormEvent } from 'react'
import { changeOwnPassword, getCurrentUser } from '../services/api'
import type { AuthenticatedUser } from '../types/tickets'
import '../styles/operations.css'

export default function Account({ token, onLogout }: { token: string; onLogout: () => void }) {
  const [account, setAccount] = useState<AuthenticatedUser | null>(null)
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    void getCurrentUser(token, controller.signal)
      .then((value) => { if (!controller.signal.aborted) setAccount(value) })
      .catch((err: unknown) => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : 'Falha ao consultar a conta.') })
    return () => controller.abort()
  }, [token])

  async function handlePasswordChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    if (newPassword !== confirmation) {
      setError('A confirmação não corresponde à nova senha.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await changeOwnPassword(token, oldPassword, newPassword)
      setOldPassword('')
      setNewPassword('')
      setConfirmation('')
      onLogout()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível atualizar a senha.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="panel operations-panel" aria-labelledby="account-title">
      <h2 id="account-title">Minha conta</h2>
      {account && (
        <div className="operations-provider">
          <strong>{account.email}</strong>
          <p>Perfil: {account.role}</p>
        </div>
      )}
      {error && <p role="alert" className="operations-error">{error}</p>}
      <form className="account-form" onSubmit={(event) => void handlePasswordChange(event)}>
        <h3>Alterar senha</h3>
        <p>Digite a senha atual e uma nova senha com no mínimo 12 caracteres.</p>
        <div className="account-form-grid">
          <label>
            Senha atual
            <input type="password" required value={oldPassword} autoComplete="current-password"
              onChange={(event) => setOldPassword(event.target.value)} disabled={saving} />
          </label>
          <label>
            Nova senha
            <input type="password" required minLength={12} maxLength={128} autoComplete="new-password"
              value={newPassword} onChange={(event) => setNewPassword(event.target.value)} disabled={saving} />
          </label>
          <label>
            Confirme a nova senha
            <input type="password" required minLength={12} maxLength={128} autoComplete="new-password"
              value={confirmation} onChange={(event) => setConfirmation(event.target.value)} disabled={saving} />
          </label>
        </div>
        <p className="operations-caption">Após a troca, você será desconectado. Tokens já emitidos podem continuar válidos até expirarem; encerre outras sessões se necessário.</p>
        <button type="submit" className="account-primary" disabled={saving}>
          {saving ? 'Atualizando...' : 'Atualizar senha'}
        </button>
      </form>
    </section>
  )
}
