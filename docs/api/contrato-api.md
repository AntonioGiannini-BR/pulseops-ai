# API FastAPI — contrato implementado

> **Estado:** endpoints implementados no código. Em desenvolvimento: base `http://127.0.0.1:8010`. Na stack Nginx: prefixo público `/api`, encaminhado para a mesma API sem prefixo. A documentação interativa `/docs` fica disponível **somente em desenvolvimento**.

## Autenticação e operação

| Método | Caminho | Perfil | Resultado |
|---|---|---|---|
| POST | `/auth/login` | Público | `access_token` JWT |
| GET | `/auth/me` | Autenticado | ID, e-mail e perfil |
| GET | `/health`, `/health/db` | Público | Saúde básica e conexão da base |
| GET | `/dashboard/summary`, `/dashboard/distribution` | Admin/analista | KPI e distribuição |
| GET | `/teams/summary` | Admin/analista | Contagens por departamento |
| GET | `/ai/status` | Admin/analista | Provedor/modelo configurado, sem revelar segredo |
| GET | `/ai/overview` | Admin/analista | Contagens agregadas de sugestões |
| GET | `/categories/` | Autenticado | Categorias ativas |
| GET | `/analysts/` | Admin | Analistas ativos |

## Chamados

| Método | Caminho | Perfil | Resultado |
|---|---|---|---|
| GET | `/tickets/`, `/tickets/{id}` | Autenticado e autorizado | Lista/consulta; solicitante só vê seus tickets |
| POST | `/tickets/` | Autenticado | Cria ticket com política SLA |
| PATCH | `/tickets/{id}` | Admin/analista | Altera prioridade e SLA |
| PATCH | `/tickets/{id}/status` | Admin/analista | Próxima transição permitida |
| PATCH | `/tickets/{id}/assign` | Admin | Atribui analista ativo |
| GET | `/tickets/{id}/history` | Autorizado | Histórico de eventos |
| GET, POST | `/tickets/{id}/comments` | Autorizado | Comentários com separação público/interno |

## IA e resolução assistida

| Método | Caminho | Perfil | Resultado |
|---|---|---|---|
| GET, POST | `/tickets/{id}/ai-suggestions` | Admin/analista | Consultar/criar sugestão pendente |
| POST | `/tickets/{id}/ai-suggestions/{suggestion_id}/review` | Admin/analista | Aprovar/rejeitar com auditoria |
| POST | `/tickets/{id}/resolution-guide` | Admin/analista | Guia textual para revisão |
| GET | `/tickets/{id}/resolution-automations` | Admin/analista | Ações disponíveis e prévias |
| POST | `/tickets/{id}/resolution-automations/{action_id}/execute` | Admin/analista | Executa ação definida no servidor após confirmação |

O corpo obrigatório para execução controlada é `{"approved":true,"expected_status":"aberto"}` (o estado deve coincidir com a prévia). Ações não podem ser inventadas pelo LLM. Chamado concluído não recebe automações. O backend não acessa sistemas externos.

## Exemplos

Autenticação:

```json
{"email":"admin@exemplo.local","password":"DIGITE_SUA_SENHA_PRIVADA"}
```

Criação:

```json
{"title":"Falha no sistema de vendas","description":"Operação indisponível na filial","requester_id":1,"category_id":2,"priority":"alta"}
```

Erros seguem HTTP 401 (não autenticado), 403 (sem perfil), 404 (não encontrado), 409 (conflito), 422 (validação), 502 (resposta inválida da IA) ou 503 (indisponibilidade), conforme a rota. Não há paginação server-side nem API pública de redefinição de senha; ambos são candidatos a evolução empresarial.
