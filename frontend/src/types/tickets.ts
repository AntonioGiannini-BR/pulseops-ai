export type TicketPriority =
  | 'baixa'
  | 'media'
  | 'alta'
  | 'critica'

export type TicketStatus =
  | 'aberto'
  | 'em_triagem'
  | 'em_atendimento'
  | 'resolvido'
  | 'fechado'

export type TicketSlaStatus =
  | 'sem_prazo'
  | 'em_dia'
  | 'atrasado'
  | 'dentro_do_prazo'
  | 'fora_do_prazo'

export interface Ticket {
  id: number
  title: string
  description: string
  priority: TicketPriority
  status: TicketStatus
  requester_id: number
  assignee_id: number | null
  category_id: number
  opened_at: string
  due_at: string | null
  resolved_at: string | null
  sla_status?: TicketSlaStatus
}

export interface TicketCreate {
  title: string
  description: string
  requester_id: number
  category_id: number
  priority: TicketPriority
}


export interface TicketHistoryEvent {
  id: number
  ticket_id: number
  actor_id: number | null
  action: string
  old_value: string | null
  new_value: string | null
  details: Record<string, unknown>
  created_at: string
}


export interface TicketComment {
  id: number
  ticket_id: number
  author_id: number
  body: string
  is_internal: boolean
  created_at: string
}


export interface TicketCommentCreate {
  body: string
  is_internal: boolean
}


export interface Category {
  id: number
  name: string
}


export interface AuthenticatedUser {
  id: number
  email: string
  role: 'admin' | 'analista' | 'solicitante'
}

export interface Analyst {
  id: number
  email: string
}
