# Dashboard Operacional — PulseOps AI

## 1. Visão geral

O Dashboard Operacional disponibiliza indicadores
sobre os chamados registrados no PulseOps AI.

Os dados são consultados diretamente no PostgreSQL
por meio de endpoints REST desenvolvidos com FastAPI.

## 2. Autenticação e autorização

Todos os endpoints exigem autenticação JWT.

Perfis autorizados:
- admin
- analista

O perfil solicitante não possui acesso aos
indicadores operacionais gerais.

## 3. Indicadores gerais

### GET /dashboard/summary

Retorna os principais indicadores da operação.

Campos:

| Campo | Descrição |
|---|---|
| total_chamados | Quantidade total de chamados |
| chamados_pendentes | Chamados ainda não concluídos |
| chamados_concluidos | Chamados resolvidos ou fechados |
| chamados_fora_sla | Chamados classificados como fora do SLA |
| horas_medias_resolucao | Tempo médio de resolução em horas |

Origem dos dados:

`v_dashboard_kpis`

## 4. Distribuição de chamados

### GET /dashboard/distribution

Retorna a quantidade de chamados agrupados
por status e prioridade.

Status disponíveis:
- aberto
- em_triagem
- em_atendimento
- resolvido
- fechado

Prioridades disponíveis:
- baixa
- media
- alta
- critica

Os agrupamentos são calculados diretamente
na tabela `tickets`.

## 5. Segurança

Os endpoints utilizam a dependência
`require_roles("admin", "analista")`.

Respostas esperadas:

| HTTP | Significado |
|---|---|
| 200 | Consulta realizada com sucesso |
| 401 | Autenticação ausente ou inválida |
| 403 | Perfil sem permissão |

## 6. Testes automatizados

Arquivo:

`backend/tests/test_dashboard.py`

Os testes verificam:

- Acesso de administradores.
- Acesso de analistas.
- Bloqueio de solicitantes.
- Bloqueio de usuários não autenticados.
- Consistência das distribuições.

Resultado da execução em 03/11/2026:

- 8 testes específicos do Dashboard aprovados.
- 59 testes do backend aprovados.

## 7. Tecnologias

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pytest
- JWT

## 8. Próximas evoluções

- Indicadores de SLA por prioridade.
- Evolução temporal dos chamados.
- Métricas individuais por analista.
- Filtros por período.
- Integração com frontend React.
- Gráficos interativos.