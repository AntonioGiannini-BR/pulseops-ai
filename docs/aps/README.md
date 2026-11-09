# APS 2026 — Projeto Final: Análise e Evolução de Sistemas de Software

**Base real:** PulseOps AI; evolução da triagem assistida de chamados. Esta pasta contém fontes UML editáveis; o relatório PDF está no pacote acadêmico entregue à equipe, não é requisito de build da API.

## Foco técnico

- GoF **Factory Method** (criacional): `TriageFactory` com subclasses concretas.
- GoF **Facade** (estrutural): `TriageFacade.generate`.
- GoF **Strategy** (comportamental): `TriageStrategy` e estratégias Mock/Ollama/OpenAI.
- SOLID: SRP, OCP (parcial; registro de fábricas precisa mudar), DIP.
- GRASP: Controller e Information Expert.
- Regressão de triagem: `backend/tests/test_aps_patterns.py`.
- Métricas: `python scripts/aps_metrics.py backend/app/services/triage_patterns.py backend/app/services/ai_triage.py`.
- Cobertura reprodutível: workflow `APS Quality Evidence`, com `pytest-cov`.

## Dados de avaliação (CI em 2026-11-09)

- 116 testes aprovados, 1 warning.
- Cobertura combinada dos módulos `ai_triage.py` (91%) e `triage_patterns.py` (98%): **93%**. Não é cobertura do sistema todo.
- CC média em `triage_patterns.py`: 1,27; CBO médio (AST aproximado): 1,56; LCOM4 médio: 1.
- CC média em `ai_triage.py`: 3,60.
- Workflow: https://github.com/AntonioGiannini-BR/pulseops-ai/actions/runs/42698744338

## Diagramas UML

- [Classes de projeto](uml/01-classes-projeto.puml): fábricas, estratégias, fachada, contrato e domínio.
- [Sequência de sugestão](uml/02-sequencia-gerar-sugestao.puml): da UI à persistência pendente.
- [Sequência de revisão](uml/03-sequencia-revisar-sugestao.puml): aprovação humana, SLA, auditoria e rollback.

Os diagramas incluem modelagem de domínio conceitual; **Chamado e SugestaoIA não são classes Python ORM**. Renderizar com PlantUML para obter imagens oficiais atualizadas.

## TDD / evidência

1. `51bf7073`: testes foram commitados antes do módulo (estado RED por importação ausente; não existe execução RED anexada).
2. `ba5379b` e `0ddbb81`: implementação e integração.
3. `c151f47`: correção da fixture de teste.
4. Execução automatizada final: 116 testes aprovados.

Para capturar RED de verdade, criar worktree temporário no commit de testes e executar `python -m pytest backend/tests/test_aps_patterns.py -q` no ambiente com dependências. **Não execute contra banco pessoal**.

## Integridade acadêmica

O enunciado define equipe de cinco pessoas, PDF até 24/11/2026 e apresentação de 5 minutos em 26/11/2026. O PDF deve conter nome completo e matrícula de todos. A regra de penalização por mais de 30% de texto gerado por IA exige reescrita e revisão autoral dos integrantes antes da entrega.

Este desenvolvimento não implica deploy público e não implementa correções em sistemas externos.
