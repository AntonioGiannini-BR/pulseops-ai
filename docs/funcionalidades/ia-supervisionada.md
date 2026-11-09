# Triagem assistida com revisão humana (US-08)

## Situação

O módulo de triagem permite que um **analista ou administrador** solicite uma sugestão para um chamado aberto, veja a prioridade/categoria recomendadas, o resumo e a justificativa, e decida aprovar ou rejeitar. **Nenhuma sugestão altera um chamado automaticamente.**

O banco `ai_suggestions` já existe no esquema inicial; este módulo não exige uma nova tabela nem executar `db/init/01_schema.sql` novamente.

## Modos de operação

| Modo | Variáveis no `backend/.env` | Comportamento |
|---|---|---|
| Demonstração (padrão) | `AI_PROVIDER=mock` | Heurística local determinística por palavras-chave; **não é um modelo de IA** |
| Modelo externo | `AI_PROVIDER=openai`, `OPENAI_API_KEY=...`, `AI_MODEL=gpt-4o-mini` | Requisição ao provedor configurado; necessita rede e chave válida |

`AI_TIMEOUT_SECONDS=10` limita a espera (2 a 30 segundos). A chave fica **somente no backend** e não deve ser adicionada ao Git nem a variáveis `VITE_*`.

O modo OpenAI usa a API de Chat Completions com resposta JSON e validação de esquema. O nome do modelo é configurável. Antes de habilitar a API externa, confirme permissões de uso, custos e política de dados da sua organização.

## Endpoints

Todos exigem JWT e perfil `admin` ou `analista`.

- `GET /tickets/{ticket_id}/ai-suggestions` — lista sugestões e decisões anteriores.
- `POST /tickets/{ticket_id}/ai-suggestions` — solicita e persiste uma sugestão `pendente` (HTTP 201).
- `POST /tickets/{ticket_id}/ai-suggestions/{suggestion_id}/review` — recebe `{"decision":"aprovada"}` ou `{"decision":"rejeitada"}`.

O botão **Gerar sugestão** faz uma chamada explícita. Uma nova sugestão não pode ser gerada enquanto houver outra pendente no mesmo chamado (HTTP 409). Chamados resolvidos/fechados não recebem novas sugestões nem aprovação, mas podem ter uma sugestão rejeitada.

**Ao aprovar:** prioridade e categoria são atualizadas em uma transação junto à revisão e à auditoria. Se a prioridade mudar, `due_at` é recalculado com `sla_policies`, desde `opened_at`. Ao rejeitar, o chamado permanece intacto. Repetir uma revisão retorna HTTP 409.

## Privacidade e falhas

- Apenas título e até 1.500 caracteres da descrição, categoria atual e categorias permitidas são enviados ao modelo externo. Comentários, histórico, identidade do solicitante e JWT **não** são enviados.
- E-mails e sequências numéricas comuns são parcialmente mascarados; isso **não garante anonimização completa**. Use dados fictícios em demonstrações e não envie informações sensíveis sem autorização.
- O texto do chamado é tratado como entrada não confiável; a resposta é validada por tipo, tamanho, prioridade e categoria ativa. A revisão humana continua obrigatória.
- Timeout/falha do provedor retorna HTTP 503; resposta inválida retorna HTTP 502. **Não há fallback silencioso** para sugestões fictícias e o atendimento normal continua funcionando.
- O histórico registra `ai_sugestao_criada`, `ai_sugestao_aprovada` ou `ai_sugestao_rejeitada`, além das alterações reais de prioridade e categoria.

## Testes

O workflow `Backend Tests` executa os testes de integração, inclusive `backend/tests/test_ai_triage.py`, com PostgreSQL isolado no GitHub Actions. O workflow `Frontend Build` valida TypeScript/Vite.

Para testar manualmente, inicie o backend e frontend, entre como analista/admin, abra um chamado em andamento, clique em **Gerar sugestão** e aprove/rejeite. Confira `ticket_history`, `ai_suggestions`, prioridade, categoria e SLA após atualizar a página.

**Limitações atuais:** não há proteção de frequência global, painel de custos, análise de anexos, anonimização garantida nem testes end-to-end em navegador. Para produção, esses pontos e a política de retenção de dados precisam de revisão.
