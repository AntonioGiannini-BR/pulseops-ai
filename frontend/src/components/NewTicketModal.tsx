import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  createTicket,
  getCategories,
  getCurrentUser,
} from '../services/api'
import type {
  AuthenticatedUser,
  Category,
  Ticket,
  TicketPriority,
} from '../types/tickets'

import '../styles/new-ticket-modal.css'

interface NewTicketModalProps {
  token: string
  onClose: () => void
  onCreated: (ticket: Ticket) => void
}

export default function NewTicketModal({
  token,
  onClose,
  onCreated,
}: NewTicketModalProps) {
  const [categories, setCategories] = useState<Category[]>([])
  const [user, setUser] = useState<AuthenticatedUser | null>(null)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [categoryId, setCategoryId] = useState<number | ''>('')
  const [priority, setPriority] = useState<TicketPriority>('media')

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadData() {
      try {
        const [categoriesData, userData] = await Promise.all([
          getCategories(token, controller.signal),
          getCurrentUser(token, controller.signal),
        ])

        if (!controller.signal.aborted) {
          setCategories(categoriesData)
          setUser(userData)
          setCategoryId(categoriesData[0]?.id ?? '')
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Erro ao carregar o formulário.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadData()

    return () => controller.abort()
  }, [token])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (saving || !user || categoryId === '') return

    if (!title.trim() || !description.trim()) {
      setError('Preencha o título e a descrição.')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const ticket = await createTicket(token, {
        title: title.trim(),
        description: description.trim(),
        requester_id: user.id,
        category_id: categoryId,
        priority,
      })

      onCreated(ticket)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Não foi possível criar o chamado.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      className="new-ticket-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !saving) {
          onClose()
        }
      }}
    >
      <section
        className="new-ticket-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-ticket-title"
      >
        <header className="new-ticket-header">
          <div>
            <span className="eyebrow">PULSEOPS / CHAMADOS</span>
            <h2 id="new-ticket-title">Novo chamado</h2>
            <p>Registre uma nova solicitação de atendimento.</p>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            aria-label="Fechar formulário"
          >
            ✕
          </button>
        </header>

        {loading && (
          <p role="status">Carregando informações...</p>
        )}

        {error && (
          <p className="new-ticket-error" role="alert">
            {error}
          </p>
        )}

        {!loading && user && categories.length > 0 && (
          <form onSubmit={handleSubmit}>
            <label htmlFor="new-ticket-title-input">
              Título
            </label>
            <input
              id="new-ticket-title-input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Ex.: Computador não conecta à rede"
              maxLength={180}
              required
              disabled={saving}
            />

            <label htmlFor="new-ticket-description">
              Descrição
            </label>
            <textarea
              id="new-ticket-description"
              value={description}
              onChange={(event) =>
                setDescription(event.target.value)
              }
              placeholder="Descreva o problema encontrado..."
              rows={5}
              required
              disabled={saving}
            />

            <div className="new-ticket-grid">
              <div>
                <label htmlFor="new-ticket-category">
                  Categoria
                </label>
                <select
                  id="new-ticket-category"
                  value={categoryId}
                  onChange={(event) =>
                    setCategoryId(Number(event.target.value))
                  }
                  required
                  disabled={saving}
                >
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="new-ticket-priority">
                  Prioridade
                </label>
                <select
                  id="new-ticket-priority"
                  value={priority}
                  onChange={(event) =>
                    setPriority(event.target.value as TicketPriority)
                  }
                  disabled={saving}
                >
                  <option value="baixa">Baixa</option>
                  <option value="media">Média</option>
                  <option value="alta">Alta</option>
                  <option value="critica">Crítica</option>
                </select>
              </div>
            </div>

            <p className="new-ticket-requester">
              Solicitante: {user.email}
            </p>

            <footer className="new-ticket-footer">
              <button
                type="button"
                className="new-ticket-cancel"
                onClick={onClose}
                disabled={saving}
              >
                Cancelar
              </button>

              <button
                type="submit"
                className="new-ticket-submit"
                disabled={saving}
              >
                {saving ? 'Criando...' : 'Criar chamado'}
              </button>
            </footer>
          </form>
        )}

        {!loading && !error && categories.length === 0 && (
          <p>Nenhuma categoria ativa encontrada.</p>
        )}
      </section>
    </div>
  )
}
