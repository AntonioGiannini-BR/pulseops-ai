# Planejamento de execução — roadmap e sprints

**Horizonte sugerido:** 6 semanas, ajustável à disponibilidade de estudo. **Modo de trabalho:** tarefas pequenas, issue + branch + Pull Request; demo ao final de cada sprint. **Status observado:** apenas artefatos da Semana 1 foram preparados; teste real do banco permanece pendente.

## Objetivo de cada etapa

| Sprint | Entregável demonstrável | Dependência | Estado |
|---|---|---|---|
| 1 — Fundamentos | Requisitos, banco, protótipo e documentação | Nenhuma | Preparada; validar Docker local |
| 2 — API | Login, controle de acesso e CRUD de chamados em FastAPI | Banco testado | Pendente |
| 3 — Interface | React + TypeScript consumindo endpoints reais | API estável | Pendente |
| 4 — Analytics | KPIs SQL, filtros reais e exportação CSV | API + frontend | Pendente |
| 5 — IA supervisionada | Sugestões com aprovação humana e auditoria | CRUD + controle de acesso | Pendente |
| 6 — Entrega | Testes automatizados, CI, deploy e vídeo | Funcionalidades essenciais | Pendente |

## Backlog por sprint

### Sprint 1 — Planejar e validar a fundação

- [x] Definir problema, personas, visão do produto e limites do MVP.
- [x] Escrever histórias US-01 a US-09, critérios de aceite e NFRs.
- [x] Criar modelo relacional e diagramas das 8 tabelas.
- [x] Preparar scripts de criação, dados fictícios e consultas SQL.
- [x] Criar dashboard demonstrativo offline e configuração do Docker.
- [x] Redigir documentação de arquitetura, segurança, testes e roadmap.
- [ ] Executar `docker compose up -d` no Windows com Docker Desktop.
- [ ] Executar `./scripts/testar-banco.ps1` no PowerShell e registrar resultado.

**Demonstração:** abrir `prototype/index.html`, executar consulta à view `v_dashboard_kpis` após validar o banco e mostrar o diagrama ER.

### Sprint 2 — Back-end (prioridade P0)

- [ ] Criar estrutura FastAPI, configuração de ambiente e conexão SQLAlchemy.
- [ ] Adotar migrações Alembic sem destruir dados da demo.
- [ ] Implementar criação de usuários habilitados por procedimento seguro; seed permanece inativa.
- [ ] Implementar autenticação e autorização (`solicitante`, `analista`, `admin`).
- [ ] Implementar US-01, US-02, US-03 e US-04: endpoints de chamados, listagem paginada e atualização auditada.
- [ ] Implementar cálculo de SLA na criação; definir política ao alterar prioridade.
- [ ] Testar permissões de acesso e consistência entre ticket e histórico.

**Demonstração:** Swagger `/docs` mostrando abertura de chamado e fluxo autorizado de atualização; um solicitante não consegue ler chamado alheio.

### Sprint 3 — Front-end

- [ ] Criar projeto React + TypeScript com rotas e estado de autenticação.
- [ ] Migrar os componentes de `prototype/` para componentes reutilizáveis.
- [ ] Integrar formulário, listagem, detalhe e atualização à API.
- [ ] Criar telas de erro, loading, vazios e controles acessíveis.
- [ ] Definir interface adaptada a celular e desktop.

**Demonstração:** dois usuários com permissões distintas interagindo com os mesmos chamados persistidos.

### Sprint 4 — Indicadores e relatórios

- [ ] Implementar US-05, US-06 e US-07: SLA, comentários e painel com dados do banco.
- [ ] Implementar filtros por categoria, status, prioridade e período.
- [ ] Exportar CSV respeitando filtros e permissões (US-09).
- [ ] Testar consistência de KPIs com consultas SQL independentes.

**Demonstração:** resolver um chamado e observar o KPI alterando após recarregar a tela.

### Sprint 5 — Integração IA supervisionada

- [ ] Integrar um adaptador configurável para API de LLM (possibilitar mock local).
- [ ] Remover informações desnecessárias do prompt; limitar tamanhos e validar resposta estruturada.
- [ ] Persistir cada sugestão como `pendente`.
- [ ] Implementar revisão humana aprovar/rejeitar com histórico.
- [ ] Cobrir saída inválida, timeout e falha do provedor, sem interromper o atendimento.

**Demonstração:** recomendação aparece separada da decisão real; prioridade não muda até aprovação.

### Sprint 6 — Confiabilidade, entrega e portfólio

- [ ] Configurar CI com lint e testes automatizados.
- [ ] Executar varredura de segredos/dependências e revisão de permissão.
- [ ] Criar ambiente de demonstração HTTPS com dados fictícios.
- [ ] Revisar README, licenças das dependências e documentação das rotas reais.
- [ ] Gravar vídeo de 2–3 minutos com cenário de ponta a ponta.
- [ ] Publicar capturas e registrar indicadores **medidos**, nunca inventados.

## Fluxo no GitHub Projects

**Colunas:** `Backlog` → `Ready` → `In progress` → `In review` → `Done`.

**Campos sugeridos:** `Sprint`, `Prioridade (P0/P1/P2)`, `Módulo`, `Estimativa`, `Responsável`, `Status`. **Labels de issues:** `documentation`, `database`, `backend`, `frontend`, `security`, `ai`, `tests`, `good-first-issue`.

**Exemplo de issue:**

```md
## Tarefa
Implementar POST /api/v1/tickets

## História vinculada
US-01

## Critérios de aceite
- [ ] Token válido e solicitante obtido da sessão
- [ ] Campos obrigatórios validados
- [ ] Prazo calculado pela política de SLA
- [ ] Ticket e evento de histórico criados na mesma transação
- [ ] Testes de sucesso, validação e acesso proibido

## Dependências
Conexão de banco e autenticação prontas
```

## Definição de pronto (DoD)

Uma tarefa só passa para `Done` com: comportamento funcional, critério de aceite atendido, testes relevantes executados, ausência de segredo no commit, documentação atualizada quando necessário, revisão do diff e status real registrado no GitHub. **Checkbox de planejamento não substitui execução nem teste.**
