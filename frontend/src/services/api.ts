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
