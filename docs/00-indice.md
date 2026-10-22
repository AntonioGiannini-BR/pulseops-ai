# Índice da documentação — PulseOps AI

> **Versão da documentação:** 0.3.0 · **Etapa:** Parte 1.
> **Implementado/preparado:** protótipo offline; scripts SQL, Docker e testes de banco para executar localmente; documentação e UML.
> **Planejado:** FastAPI, autenticação, frontend React, IA generativa, deploy e testes de integração. Não apresentar recursos planejados como concluídos.

## Por onde começar

1. [README principal](../README.md) — apresentação, recursos reais e execução.
2. [Planejamento geral](planejamento/plano-geral.md) — problema, objetivos, escopo e entregas.
3. [Visão do produto](planejamento/visao-do-produto.md) — público e MVP.
4. [Requisitos e histórias](requisitos/requisitos-e-historias.md) — histórias, prioridades e critérios de aceite.
5. [Arquitetura](arquitetura/arquitetura.md) — contexto, decisões e fluxos propostos.
6. [Modelo de dados](banco-de-dados/modelagem.md) — oito tabelas e relacionamentos.
7. [Diagramas UML](uml/README.md) — fontes PlantUML e imagens.
8. [Roadmap e sprints](planejamento/roadmap-e-sprints.md) — entregas por semana.

## Por área

| Área | Documentos |
|---|---|
| Planejamento | [Plano geral](planejamento/plano-geral.md), [Visão](planejamento/visao-do-produto.md), [Roadmap](planejamento/roadmap-e-sprints.md), [Riscos/ADRs](planejamento/riscos-e-decisoes.md) |
| Requisitos | [Histórias](requisitos/requisitos-e-historias.md), [Regras de negócio](requisitos/regras-de-negocio.md) |
| Arquitetura | [Visão técnica](arquitetura/arquitetura.md), [Padrões](arquitetura/padroes-de-desenvolvimento.md), [Galeria](arquitetura/galeria-visual.md) |
| Banco de dados | [Modelagem e DER](banco-de-dados/modelagem.md), [Esquema SQL](../db/init/01_schema.sql) |
| API | [Contrato proposto](api/contrato-api.md) |
| Segurança | [Plano de segurança e privacidade](seguranca/seguranca-e-privacidade.md) |
| Testes | [Estratégia e validações](testes/plano-de-testes.md) |
| UML | [Índice de diagramas](uml/README.md) e fontes `.puml` em `docs/uml/diagramas/` |
| Contribuição | [Git e commits](contribuicao/git-e-commits.md) |

## Documentação voltada para agentes de IA

- [`llms.txt`](../llms.txt): mapa curto e seletivo das fontes autorizadas, pensado para leitura e navegação por agentes.
- [`llms-full.txt`](../llms-full.txt): conteúdo textual consolidado da documentação para fornecer contexto com mínimo esforço de navegação.
- [`DOCUMENTACAO.md`](../DOCUMENTACAO.md): síntese técnica organizada para leitura humana.
- [`scripts/validar-documentacao.py`](../scripts/validar-documentacao.py): verifica links internos, imagens e os arquivos `.puml`.

## Regras de manutenção

1. Documente cada funcionalidade junto com o código no mesmo Pull Request.
2. Atualize roadmap, contrato API, regras e testes, se forem afetados.
3. Use links relativos para que as imagens apareçam diretamente no GitHub.
4. Separe *estado atual* de *arquitetura futura* e evite resultados/testes não verificados.
5. Depois de alterar qualquer `.md`, gere novamente `llms-full.txt` com `python scripts/gerar-llms-full.py` e valide com `python scripts/validar-documentacao.py`.

## Integração contínua

O arquivo [`.github/workflows/docs.yml`](../.github/workflows/docs.yml) valida links internos e confere se `llms-full.txt` acompanha as últimas mudanças sempre que a documentação é alterada em um pull request ou push.
