# Contrato preliminar da API — Semana 2

> **Estado da documentação:** Contrato previsto; nenhum endpoint FastAPI está implementado nesta versão.

![Arquitetura-alvo da API no contexto do sistema](../imagens/02-arquitetura-alvo.png)

*API planejada, ainda não implementada nesta entrega.*

Base local sugerida: `http://localhost:8000/api/v1`.

| Método | Rota | Quem usa | Finalidade |
|---|---|---|---|
| POST | `/auth/login` | Público | Autenticação; token de sessão |
| GET | `/auth/me` | Autenticado | Dados do usuário atual |
| GET | `/tickets` | Autenticado | Listar com filtros, paginação e restrição de acesso |
| POST | `/tickets` | Solicitante/analista/admin | Criar chamado; registrar autor do token |
| GET | `/tickets/{id}` | Autorizado | Detalhar chamado |
| PATCH | `/tickets/{id}` | Analista/admin | Alterar responsável, prioridade, status; registrar histórico |
| POST | `/tickets/{id}/comments` | Autorizado | Adicionar comentário |
| GET | `/categories` | Autenticado | Listar categorias |
| GET | `/dashboard/kpis` | Analista/admin | Estatísticas agregadas |
| GET | `/dashboard/by-category` | Analista/admin | Chamados por categoria |
| POST | `/tickets/{id}/ai-suggestions` | Analista/admin | Pedir sugestão de triagem (Semana 5) |
| POST | `/ai-suggestions/{id}/review` | Analista/admin | Aprovar ou rejeitar sugestão (Semana 5) |

## Exemplo de criação de chamado (futuro)
```json
{
  "title": "Sistema de vendas fora do ar",
  "description": "Equipe não consegue registrar os pedidos.",
  "category_id": 2,
  "priority": "alta"
}
```

## Exemplo da resposta planejada (futuro)
```json
{
  "id": 9,
  "title": "Sistema de vendas fora do ar",
  "status": "aberto",
  "priority": "alta",
  "due_at": "2026-10-20T20:00:00-03:00"
}
```

**Atenção:** estas rotas são uma especificação, **não estão implementadas** nesta Parte 1. O backend FastAPI será iniciado na Parte 2.
