export interface DashboardSummary {
  total_chamados: number
  chamados_pendentes: number
  chamados_concluidos: number
  chamados_fora_sla: number
  horas_medias_resolucao: number | null
  cumprimento_sla_pct: number | null
}

export interface DashboardDistribution {
  por_status: {
    aberto: number
    em_triagem: number
    em_atendimento: number
    resolvido: number
    fechado: number
  }
  por_prioridade: {
    baixa: number
    media: number
    alta: number
    critica: number
  }
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface TeamSummary {
  id: number
  name: string
  active_users: number
  analysts: number
  tickets_total: number
  tickets_open: number
}

export interface AIOverview {
  suggestions_total: number
  pending: number
  approved: number
  rejected: number
  ollama: number
  demonstration: number
  external_models: number
}


export interface ManagedUser {
  id: number
  full_name: string
  email: string
  role: 'admin' | 'analista' | 'solicitante'
  department_id: number | null
  is_active: boolean
  created_at: string
}

export interface UserCreatePayload {
  full_name: string
  email: string
  password: string
  role: 'analista' | 'solicitante'
  department_id: number | null
}
