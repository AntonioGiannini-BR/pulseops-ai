# Documentação técnica — PulseOps AI

> **Versão:** 0.3.0 · **Situação:** Parte 1 (protótipo offline e infraestrutura SQL/Docker preparada para execução local). **Planejados:** FastAPI, React, autenticação, IA e deploy.

## Objetivo

Construir uma plataforma de gestão de chamados corporativos com histórico, responsáveis, categorias, priorização, prazos de SLA e indicadores. Evoluir para um produto full-stack com triagem por IA generativa **apenas mediante revisão humana**. O projeto é demonstrativo e voltado a aprendizado/portfólio.

## O que realmente existe

- Dashboard HTML/CSS/JavaScript offline com dados fictícios: [`prototype/`](prototype/).
- Scripts PostgreSQL com oito tabelas, views e dados demonstrativos: [`db/init/`](db/init/) e [`db/queries/`](db/queries/).
- Docker Compose preparado para rodar o PostgreSQL localmente: [`compose.yaml`](compose.yaml).
- Diagramas arquiteturais, UML editável e documentação técnica: [`docs/`](docs/00-indice.md).
- Testes de banco **incluídos, mas sem validação real neste ambiente**: [`db/tests/`](db/tests/) e [`scripts/testar-banco.ps1`](scripts/testar-banco.ps1).

## Arquitetura de referência

![Arquitetura-alvo (ainda não implementada)](docs/imagens/02-arquitetura-alvo.png)

O backend FastAPI atenderá uma interface React, armazenará dados no PostgreSQL e controlará a criação, transição e auditoria de chamados. Um serviço opcional de IA fará sugestões que não poderão ser aplicadas sem aprovação de um analista autorizado. Essas camadas são **planejadas**. Consulte a [arquitetura detalhada](docs/arquitetura/arquitetura.md).

## Modelo de domínio

O esquema contém: `departments`, `app_users`, `categories`, `sla_policies`, `tickets`, `ticket_comments`, `ticket_history` e `ai_suggestions`. O SQL é a fonte de verdade do modelo físico.

![Entidades e relacionamentos](docs/banco-de-dados/diagramas/diagrama-entidades.png)

Veja [modelagem](docs/banco-de-dados/modelagem.md) e [classes UML](docs/uml/README.md).

## Contratos, regras e segurança

- [Requisitos e casos de uso](docs/requisitos/requisitos-e-historias.md).
- [Transições de status, papéis, SLA e IA supervisionada](docs/requisitos/regras-de-negocio.md).
- [Contrato proposto da API](docs/api/contrato-api.md).
- [Segurança e privacidade](docs/seguranca/seguranca-e-privacidade.md).
- [Testes previstos e disponíveis](docs/testes/plano-de-testes.md).
- [ADRs e riscos](docs/planejamento/riscos-e-decisoes.md).

## Planejamento e decisões

O MVP seguirá entregas incrementais, com arquitetura modular e testes por etapa. A implementação futura não deve ser reportada no currículo ou no GitHub como concluída antes de estar disponível e validada.

Veja [plano geral](docs/planejamento/plano-geral.md), [roadmap](docs/planejamento/roadmap-e-sprints.md), [Git e commits](docs/contribuicao/git-e-commits.md) e [índice completo](docs/00-indice.md).

## Contexto legível por IA

- [`llms.txt`](llms.txt): entrada curta e referências prioritárias.
- [`llms-full.txt`](llms-full.txt): cópia textual consolidada dos documentos principais.
- [`scripts/gerar-llms-full.py`](scripts/gerar-llms-full.py): regeneração do arquivo após atualizar os documentos.
- [`scripts/validar-documentacao.py`](scripts/validar-documentacao.py): checagem de links e existência dos artefatos.
