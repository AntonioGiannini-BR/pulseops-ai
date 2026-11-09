# Estratégia de testes e validação — PulseOps AI

## Automatizado no GitHub Actions

| Workflow | Verificação | Escopo |
|---|---|---|
| [Backend Tests](../../.github/workflows/backend-tests.yml) | Pytest e PostgreSQL isolado; smoke SQL | CRUD, auth/RBAC, SLA, histórico, IA, automações, bootstrap, métricas |
| [Frontend Build](../../.github/workflows/frontend-build.yml) | `npm ci` e `npm run build` | TypeScript e build React/Vite |
| [Full Stack Smoke](../../.github/workflows/full-stack-smoke.yml) | Docker Compose e requisições HTTP reais | Build de API/Nginx, saúde, banco, autenticação exigida, Swagger desabilitado, cabeçalhos |
| [Validar documentação](../../.github/workflows/docs.yml) | Links/UML e `llms-full.txt` regenerado | Integridade documental |

CI confirma o que está no commit testado; **não substitui** teste humano em navegador nem teste da qualidade das respostas do Qwen no Windows.

## Validação manual obrigatória antes de release

- Login com conta válida; logout e expiração de JWT.
- Criar e localizar um chamado; alterar prioridade e conferir recálculo de SLA; avançar status e inspecionar auditoria.
- Conferir que solicitante não visualiza chamados alheios nem comentários internos.
- Exportar CSV filtrado e abrir em planilha; não interpretar títulos começando em `=`, `+`, `-` ou `@` como fórmulas.
- Acessar Equipes e Central de IA: checar indicadores e ausência de dados pessoais no resumo.
- Com `AI_PROVIDER=ollama`, gerar sugestão, rejeitar/aprovar e conferir que nenhuma ação foi executada sem aprovação.
- Gerar plano de resolução com Qwen, conferir que causa é tratada como hipótese e que etapas são revisáveis.
- Executar cada automação com confirmação explícita; verificar comentário público, histórico e que o chamado nunca é marcado como resolvido automaticamente.
- Desligar Ollama temporariamente e conferir erro controlado e continuidade do atendimento manual.
- Testar os containers em porta local, simular falha do PostgreSQL e conferir tratamento; restaurar base a partir de backup de teste.

## Comandos

No backend com PostgreSQL de teste configurado:

```powershell
cd backend
python -m pytest -q
```

No frontend:

```powershell
cd frontend
npm ci
npm run build
```

Para stack Docker privada:

```powershell
docker compose -f compose.yaml -f compose.app.yaml up -d --build --wait
Invoke-RestMethod http://127.0.0.1:8080/api/health
Invoke-RestMethod http://127.0.0.1:8080/api/health/db
```

O banco de dados local pode conter dados de teste persistentes. **Não execute `docker compose down -v` para depurar problemas de frontend/backend.** Não use `db/init/*.sql` para migrar uma base existente.

## Pendências de produção

- Suite de testes E2E automatizada em navegador (Playwright/Cypress), com cenário completo e ambiente descartável.
- Verificações de carga, observabilidade, retenção/backup, segurança independente e teste de recuperação.
- Revisão de login contra brute force em infraestrutura distribuída; o rate limit Nginx é apenas uma camada.
- Homologação de conectores corporativos futuros antes de ativar correções externas.

A documentação não afirma que uma funcionalidade foi validada manualmente sem evidência. Consulte também [o guia de release](../implantacao/guia-de-release.md).
