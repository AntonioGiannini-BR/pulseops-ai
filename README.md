# PulseOps AI — Gestão Inteligente de Operações

Projeto de portfólio para estudar engenharia de software aplicada a suporte corporativo: gestão de chamados, rastreabilidade, SLAs, métricas e, futuramente, sugestões assistidas por IA com revisão humana.

> **Status: Parte 1 — planejamento, documentação UML e protótipo.** O painel HTML/CSS/JavaScript funciona offline com dados fictícios. Esquema PostgreSQL, Docker e scripts de testes estão preparados, mas a execução do banco deve ser validada localmente. **FastAPI, React, login, integrações e IA ainda não estão implementados.**

![Prévia do protótipo do dashboard](docs/imagens/dashboard-preview.png)

## Documentação principal

- [Índice de toda a documentação](docs/00-indice.md) — comece aqui.
- [Planejamento](docs/planejamento/plano-geral.md) e [roadmap](docs/planejamento/roadmap-e-sprints.md).
- [Requisitos e histórias de usuário](docs/requisitos/requisitos-e-historias.md) e [regras de negócio](docs/requisitos/regras-de-negocio.md).
- [Arquitetura](docs/arquitetura/arquitetura.md), [galeria visual](docs/arquitetura/galeria-visual.md) e [diagramas PlantUML](docs/uml/README.md).
- [Modelagem do banco de dados](docs/banco-de-dados/modelagem.md) e [API planejada](docs/api/contrato-api.md).
- [Segurança](docs/seguranca/seguranca-e-privacidade.md), [testes](docs/testes/plano-de-testes.md) e [guia de commits](docs/contribuicao/git-e-commits.md).
- **Para IA e agentes:** [`llms.txt`](llms.txt) (mapa curto) e [`llms-full.txt`](llms-full.txt) (documentação consolidada).

## Arquitetura atual e proposta

**Parte 1:** protótipo independente do banco; scripts SQL e PostgreSQL via Docker Compose preparados para validação.

![Estado atual da Parte 1](docs/imagens/01-arquitetura-atual.png)

**Planejado:** React + TypeScript, FastAPI, PostgreSQL e modelo de IA com revisão humana.

![Arquitetura-alvo planejada](docs/imagens/02-arquitetura-alvo.png)

## Executar protótipo no Windows

1. Extraia este projeto e abra a pasta no VS Code.
2. Abra `prototype/index.html` no navegador. A interface é demonstrativa e não salva alterações no PostgreSQL.
3. Para subir o banco local, com o Docker Desktop aberto, execute no PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
# Troque POSTGRES_PASSWORD por uma senha de desenvolvimento forte antes de prosseguir
docker compose up -d
docker compose ps
.\scripts\testar-banco.ps1
```

Para entrar no banco:

```powershell
docker compose exec database sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

> **Atenção:** `docker compose down -v` apaga o volume do PostgreSQL. Os arquivos `db/init/*.sql` são aplicados somente na criação inicial do volume. Mudanças posteriores exigirão migrações.

## Fontes disponíveis

```text
prototype/         HTML, CSS e JavaScript da demonstração
db/init/           Esquema e dados fictícios para PostgreSQL
db/queries/        Consultas analíticas
db/tests/          Testes SQL preparados
compose.yaml       Serviço local PostgreSQL
scripts/           Verificação do banco, renderização UML e validação dos docs
docs/              Planejamento, arquitetura, UML e imagens
llms.txt           Navegação resumida para LLMs
llms-full.txt      Contexto textual consolidado
```

## Qualidade e segurança

- Não publique `.env`, credenciais ou dados reais de clientes.
- Os dados do protótipo são fictícios e não constituem autenticação ou sistema pronto para produção.
- Autenticação, autorização, proteção de API, logs de auditoria e testes end-to-end são **objetivos futuros**.
- A renderização das fontes PlantUML oficiais depende de Java + JAR PlantUML no computador. As imagens existentes são prévias e não substituem a validação dessas fontes.

## Verificar a documentação

A ação [Validar documentação](.github/workflows/docs.yml) também executa essas verificações automaticamente no GitHub.

```powershell
python scripts/gerar-llms-full.py
python scripts/validar-documentacao.py
```

[Documentação técnica consolidada](DOCUMENTACAO.md) · [Guia de Git e commits](docs/contribuicao/git-e-commits.md)
