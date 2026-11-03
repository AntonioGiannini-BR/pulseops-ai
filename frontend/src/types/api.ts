export interface DashboardSummary {
  total_chamados: number
  chamados_pendentes: number
  chamados_concluidos: number
  chamados_fora_sla: number
  horas_medias_resolucao: number | null
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
