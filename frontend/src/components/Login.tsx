import { useState, type FormEvent } from 'react'
import { login } from '../services/api'
import '../styles/login.css'

interface LoginProps {
  onAuthenticated: (token: string) => void
}

export default function Login({ onAuthenticated }: LoginProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await login(email.trim(), password)
      onAuthenticated(response.access_token)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Não foi possível realizar o login.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-screen">
      <div className="login-layout">
        <section className="login-presentation">
          <div className="login-brand">
            <div className="login-brand-icon">P</div>
            <span>PulseOps <strong>AI</strong></span>
          </div>

          <div className="login-presentation-content">
            <span className="login-eyebrow">
              INTELIGÊNCIA OPERACIONAL
            </span>

            <h1>
              Transforme dados em
              <span> decisões inteligentes.</span>
            </h1>

            <p>
              Centralize operações, acompanhe indicadores
              e tenha mais controle sobre seus chamados
              em uma única plataforma.
            </p>

            <div className="login-features">
              <div className="login-feature">
                <span className="login-feature-icon">↗</span>
                <span>Indicadores em tempo real</span>
              </div>

              <div className="login-feature">
                <span className="login-feature-icon">✓</span>
                <span>Gestão de chamados e SLA</span>
              </div>

              <div className="login-feature">
                <span className="login-feature-icon">✦</span>
                <span>Operações orientadas por dados</span>
              </div>
            </div>
          </div>

          <div className="login-presentation-footer">
            PULSEOPS AI · PLATAFORMA DE OPERAÇÕES
          </div>
        </section>

        <section className="login-form-section">
          <div className="login-form-container">
            <div className="login-form-heading">
              <span className="login-form-badge">
                ACESSO À PLATAFORMA
              </span>

              <h2>Bem-vindo de volta</h2>

              <p>
                Entre com suas credenciais para acessar
                o painel de operações.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="login-form">
              <div className="login-field">
                <label htmlFor="login-email">
                  E-mail
                </label>

                <input
                  id="login-email"
                  type="email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="username"
                  required
                  disabled={loading}
                />
              </div>

              <div className="login-field">
                <label htmlFor="login-password">
                  Senha
                </label>

                <div className="login-password-wrapper">
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Digite sua senha"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="current-password"
                    required
                    disabled={loading}
                  />

                  <button
                    type="button"
                    className="login-password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={
                      showPassword
                        ? 'Ocultar senha'
                        : 'Mostrar senha'
                    }
                  >
                    {showPassword ? 'Ocultar' : 'Mostrar'}
                  </button>
                </div>
              </div>

              {error && (
                <div className="login-error" role="alert">
                  {error}
                </div>
              )}

              <button
                type="submit"
                className="login-submit"
                disabled={loading}
              >
                {loading ? 'Entrando...' : 'Entrar na plataforma'}
                {!loading && <span aria-hidden="true">→</span>}
              </button>
            </form>

            <div className="login-security">
              <span aria-hidden="true">◆</span>
              Acesso protegido por autenticação JWT
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
