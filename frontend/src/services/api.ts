import type { Analyst, TicketAISuggestion, TicketAIReviewResult, AIReviewStatus } from '../types/tickets'
import type { Category, AuthenticatedUser } from '../types/tickets'
import type { TicketCreate } from '../types/tickets'
import type { Ticket, TicketHistoryEvent, TicketComment, TicketCommentCreate } from '../types/tickets'
import type {
  DashboardSummary,
  DashboardDistribution,
  LoginResponse,
} from '../types/api'

const API_URL = import.meta.env.VITE_API_URL

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  if (!API_URL) {
    throw new Error('Endereço da API não configurado.')
  }

  let response: Response

  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
  } catch {
    throw new Error(
      'Não foi possível conectar ao servidor. Verifique se o FastAPI está ativo.',
    )
  }

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error(path === '/auth/login' ? 'E-mail ou senha inválidos.' : 'Sessão inválida ou expirada. Faça login novamente.')
    }

    if (response.status === 403) {
      throw new Error('Você não possui permissão para acessar esses dados.')
    }

    const data: unknown = await response.json().catch(() => null)
    if (data && typeof data === 'object' && 'detail' in data &&
        typeof data.detail === 'string' && data.detail.length <= 200) {
      throw new Error(data.detail)
    }
    throw new Error(`Erro na API: HTTP ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getDashboardSummary(
  token: string,
  signal?: AbortSignal,
): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>('/dashboard/summary', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal,
  })
}

export function getDashboardDistribution(
  token: string,
  signal?: AbortSignal,
): Promise<DashboardDistribution> {
  return apiRequest<DashboardDistribution>('/dashboard/distribution', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal,
  })
}


export function getTickets(
  token: string,
  signal?: AbortSignal,
): Promise<Ticket[]> {
  return apiRequest<Ticket[]>('/tickets/', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal,
  })
}


export function getTicket(
  token: string,
  ticketId: number,
  signal?: AbortSignal,
): Promise<Ticket> {
  return apiRequest<Ticket>(`/tickets/${ticketId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal,
  })
}


export function getTicketHistory(
  token: string,
  ticketId: number,
  signal?: AbortSignal,
): Promise<TicketHistoryEvent[]> {
  return apiRequest<TicketHistoryEvent[]>(
    `/tickets/${ticketId}/history`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal,
    },
  )
}


export function getTicketComments(
  token: string,
  ticketId: number,
  signal?: AbortSignal,
): Promise<TicketComment[]> {
  return apiRequest<TicketComment[]>(
    `/tickets/${ticketId}/comments`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal,
    },
  )
}


export function createTicketComment(
  token: string,
  ticketId: number,
  payload: TicketCommentCreate,
): Promise<TicketComment> {
  return apiRequest<TicketComment>(
    `/tickets/${ticketId}/comments`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    },
  )
}


export function createTicket(
  token: string,
  payload: TicketCreate,
): Promise<Ticket> {
  return apiRequest<Ticket>('/tickets/', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })
}


export function getCategories(
  token: string,
  signal?: AbortSignal,
): Promise<Category[]> {
  return apiRequest<Category[]>('/categories/', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal,
  })
}


export function getCurrentUser(
  token: string,
  signal?: AbortSignal,
): Promise<AuthenticatedUser> {
  return apiRequest<AuthenticatedUser>('/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal,
  })
}


export function updateTicketStatus(
  token: string,
  ticketId: number,
  status: Ticket['status'],
): Promise<Pick<Ticket, 'id' | 'status' | 'resolved_at' | 'due_at'>> {
  return apiRequest<Pick<Ticket, 'id' | 'status' | 'resolved_at' | 'due_at'>>(
    `/tickets/${ticketId}/status`,
    {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ status }),
    },
  )
}


export function updateTicketPriority(
  token: string,
  ticketId: number,
  priority: Ticket['priority'],
): Promise<Pick<Ticket, 'id' | 'priority' | 'due_at'>> {
  return apiRequest<Pick<Ticket, 'id' | 'priority' | 'due_at'>>(
    `/tickets/${ticketId}`,
    {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ priority }),
    },
  )
}

export function getAnalysts(
  token: string,
  signal?: AbortSignal,
): Promise<Analyst[]> {
  return apiRequest<Analyst[]>('/analysts/', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal,
  })
}


export function assignTicket(
  token: string,
  ticketId: number,
  assigneeId: number,
): Promise<Pick<Ticket, 'id' | 'assignee_id'>> {
  return apiRequest<Pick<Ticket, 'id' | 'assignee_id'>>(
    `/tickets/${ticketId}/assign`,
    {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ assignee_id: assigneeId }),
    },
  )
}

export function getTicketAISuggestions(
  token: string,
  ticketId: number,
  signal?: AbortSignal,
): Promise<TicketAISuggestion[]> {
  return apiRequest<TicketAISuggestion[]>(`/tickets/${ticketId}/ai-suggestions`, {
    headers: { Authorization: `Bearer ${token}` },
    signal,
  })
}

export function generateTicketAISuggestion(
  token: string,
  ticketId: number,
): Promise<TicketAISuggestion> {
  return apiRequest<TicketAISuggestion>(`/tickets/${ticketId}/ai-suggestions`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
}

export function reviewTicketAISuggestion(
  token: string,
  ticketId: number,
  suggestionId: number,
  decision: Exclude<AIReviewStatus, 'pendente'>,
): Promise<TicketAIReviewResult> {
  return apiRequest<TicketAIReviewResult>(
    `/tickets/${ticketId}/ai-suggestions/${suggestionId}/review`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ decision }),
    },
  )
}
