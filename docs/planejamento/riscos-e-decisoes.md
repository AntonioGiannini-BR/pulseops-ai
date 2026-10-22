# Riscos, premissas e registros de decisões (ADR)

**Estado:** decisões de projeto adotadas para planejar o MVP. Itens marcados como proposta não significam código implementado.

## 1. Premissas

- MVP de **empresa única**, com registros demonstrativos fictícios.
- Equipe de desenvolvimento pequena/individual, recursos computacionais locais, orçamento restrito.
- SLA em **horas corridas**, sem feriados e dias úteis na versão inicial.
- A IA oferece recomendações; um usuário autorizado mantém o controle.
- O protótipo HTML atual não é a interface final nem usa API.

## 2. Registro de riscos

| ID | Risco | Probabilidade / Impacto | Mitigação e gatilho |
|---|---|---|---|
| R-01 | Escopo grande impede conclusão | Alta / Alta | Priorizar P0, adiar IA avançada; demo mínima na Sprint 2–3 |
| R-02 | Diferença entre documentação e implementação | Média / Alta | Atualizar docs no PR, marcar planos vs feitos |
| R-03 | Falha de ambiente Docker/PostgreSQL | Média / Média | Testar seed e smoke tests cedo; registrar versões |
| R-04 | Acesso indevido a chamados | Média / Alta | Autorização por recurso, testes negativos por perfil |
| R-05 | Vazamento de dados à IA externa | Média / Alta | Dados fictícios, minimização e revisão de política do provedor |
| R-06 | Saída incorreta/alucinada da IA | Alta / Média | Schema fechado, revisão humana, sem execução automática |
| R-07 | SLA incorreto por data/fuso | Média / Alta | UTC interno, testes de limites, documentar regra de alteração |
| R-08 | Dependência excessiva da API de IA | Média / Média | Adaptador/mocks, timeout, fallback manual |
| R-09 | Deploy sem segurança | Média / Alta | Checklist de release e bloqueio de publicação até testes mínimos |

Revisar riscos por sprint, atualizando **status, impacto e evidências** (issues/PRs).

## 3. Decisões arquiteturais (ADR)

### ADR-001 — Monólito modular no MVP

- **Status:** aceito para planejamento (2026-10-20).
- **Contexto:** pequeno projeto de portfólio, sem requisitos comprovados de escala horizontal entre módulos.
- **Decisão:** uma API FastAPI organizada em camadas e módulos, em vez de diversos microsserviços.
- **Consequências:** reduz operação e facilita testes; serviços só serão separados se surgir necessidade mensurável.

### ADR-002 — PostgreSQL como base relacional

- **Status:** aceito para Parte 1.
- **Contexto:** entidades ligadas, consultas de indicadores, chaves estrangeiras e transações.
- **Decisão:** PostgreSQL 17 com `TIMESTAMPTZ`, restrições e índices; SQLAlchemy/Alembic planejados.
- **Alternativa:** SQLite, suficiente para demonstração simples, mas com menor equivalência ao uso empresarial multiusuário pretendido.
- **Consequência:** requer Docker/configuração local, em troca de SQL e integridade fortes.

### ADR-003 — React + TypeScript e FastAPI

- **Status:** proposto; implementação pendente.
- **Decisão:** interface baseada em componentes tipados e API Python separada.
- **Razão:** demonstrar desenvolvimento full-stack, documentação OpenAPI e uso de Python para análises futuras.
- **Consequência:** duas bases de código e mais ferramentas de build/teste; protótipo atual será migrado.

### ADR-004 — IA human-in-the-loop

- **Status:** aceito como requisito; implementação pendente.
- **Decisão:** persistir recomendação de IA em estado `pendente`; somente pessoa autorizada pode aplicá-la.
- **Razão:** reduzir risco operacional, permitir auditoria e demonstrar controle humano.
- **Consequência:** fluxo adiciona uma etapa, mas evita ações silenciosas por saída de modelo.

### ADR-005 — Regra inicial de SLA

- **Status:** parcialmente decidido; validar antes da API.
- **Decisão atual:** usar minutos corridos a partir de `opened_at` e política da prioridade.
- **Questão aberta:** ao mudar prioridade, recalcular prazo a partir da abertura, guardar o prazo original e registrar alteração? **Proposta inicial:** recalcular a partir da abertura e auditar mudança.
- **Consequência:** simples e determinístico, mas não contempla jornadas comerciais e escalonamentos complexos.

### ADR-006 — Controle de histórico

- **Status:** recomendação para implementação.
- **Decisão:** excluir fisicamente tickets não será permitido via API; mudanças relevantes gravam histórico na mesma transação.
- **Ponto de atenção:** `ON DELETE CASCADE` já existe em algumas FKs da base preparada e deve ser revisado se houver requisitos formais de retenção/auditoria.

## 4. Modelo para novas decisões

```md
### ADR-00X — Título da decisão
- Status: proposto | aceito | substituído
- Contexto: qual problema estamos resolvendo?
- Alternativas: o que foi considerado?
- Decisão: qual opção foi escolhida?
- Consequências: vantagens, custos e riscos.
- Referências: issue/PR e data.
```

**Princípio:** preferir justificar decisões com critérios verificáveis, sem afirmar que toda escolha representa uma exigência específica da Accenture.
