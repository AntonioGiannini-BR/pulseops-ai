# Plano do projeto — PulseOps AI

**Documento:** termo de abertura e plano executivo de desenvolvimento.  
**Versão:** 0.2 (Parte 1) • **Responsável:** mantenedor do repositório.  
**Status:** planejamento em andamento; protótipo offline e scripts SQL preparados, banco pendente de validação local.

## 1. Resumo e motivação

**Problema:** solicitações e incidentes empresariais dispersos em planilhas e mensagens dificultam priorização, rastreabilidade, gestão de prazos e acompanhamento gerencial.

**Solução proposta:** desenvolver uma plataforma web de chamados com autenticação, fluxo de atendimento, métricas reais e assistência opcional de IA para triagem supervisionada.

**Público-alvo:** solicitantes, analistas de suporte e administradores; visão executiva de KPIs via perfil administrador no MVP.

## 2. Objetivo geral e objetivos específicos

**Objetivo geral:** criar um MVP demonstrável, reproduzível e seguro o suficiente para um ambiente **de desenvolvimento/demonstração**, que percorra o ciclo de vida de um chamado do cadastro à resolução e aos indicadores.

Objetivos verificáveis:

1. Permitir que contas ativas e autorizadas criem, filtrem, atribuam, atualizem e resolvam chamados.
2. Implementar regras de SLA e histórico das mudanças na API e no PostgreSQL.
3. Substituir os dados estáticos do protótipo por informações reais da API.
4. Produzir e documentar testes de integridade, domínio, integração e segurança de acesso.
5. Disponibilizar instruções de execução e um vídeo com um fluxo de ponta a ponta usando **dados fictícios**.
6. Caso a integração de IA seja feita, exigir validação humana e apresentar resultados medidos, não presumidos.

## 3. Entregas principais e critérios de aceite

| Entregável | Resultado verificável | Estado atual |
|---|---|---|
| Documento de visão, requisitos e arquitetura | Markdown revisável + diagramas | Preparado |
| Modelo de dados e SQL | Scripts de 8 tabelas, views, seed e testes | Preparado; execução local pendente |
| Ambiente PostgreSQL | `docker compose up -d` + smoke tests | Preparado; execução local pendente |
| Interface navegável de demonstração | Abre no navegador e utiliza dados fictícios | Disponível offline |
| API FastAPI | Rotas versionadas, schemas e documentação Swagger | Planejado |
| Fluxos autenticados | Permissões aplicadas no servidor e histórico atômico | Planejado |
| Front-end React integrado | Criar/listar/atualizar chamados no banco | Planejado |
| Indicadores reais | Métricas conferidas contra SQL | Planejado |
| IA com aprovação humana | Sugestão registrada, aprovada/rejeitada explicitamente | Planejado |
| Publicação e CI | Testes automatizados, deploy e README reproduzível | Planejado |

## 4. Escopo

**Dentro do MVP:** autenticação, permissões por perfil, CRUD controlado de chamados, comentários, histórico, SLA por horas corridas, dashboard, API REST, testes e documentação; IA de triagem como última melhoria funcional.

**Fora do MVP:** sistema multiempresa, aplicação móvel nativa, integração com clientes reais, anexos e SSO, SLA com calendário comercial, execução automática de ações propostas por IA.

## 5. Premissas, restrições e dependências

- Desenvolvimento individual ou equipe pequena; estimativas semanais são **referências adaptáveis**, não prazos garantidos.
- Disponibilidade de VS Code, Git e Docker Desktop para banco local.
- Banco e dados de teste não devem conter informações pessoais reais.
- Custos de hospedagem e provedores de LLM podem mudar; escolher opções e limites antes de ativá-los.
- A documentação descreve o planejamento; **não demonstra por si só que a implementação está concluída**.

Dependências críticas: validar PostgreSQL antes da API; construir autenticação/CRUD antes de conectar React; ter fluxo básico funcional antes da IA; possuir testes mínimos antes de deploy.

## 6. Estratégia de execução

Dividir as atividades em issues pequenas num quadro Kanban; usar branches temáticas e PRs; aplicar a definição de pronto em cada sprint; priorizar P0 (essencial) e só então P1/P2 (aprimoramentos). Ver [roadmap detalhado](roadmap-e-sprints.md).

```mermaid
flowchart LR
    P1[1. Planejar + modelar] --> P2[2. API + autenticação]
    P2 --> P3[3. React + integração]
    P3 --> P4[4. Indicadores]
    P4 --> P5[5. IA supervisionada]
    P5 --> P6[6. Testes finais + deploy]
```

## 7. Indicadores de sucesso do projeto

Não há valores de desempenho medidos nesta fase. As metas abaixo são **critérios de entrega**, e não resultados alcançados:

- **Reprodutibilidade:** outro desenvolvedor consegue subir o banco e rodar o fluxo seguindo o README.
- **Qualidade:** testes críticos passam localmente e no pipeline quando for configurado.
- **Rastreabilidade:** mudanças relevantes incluem histórico e documentação atualizada.
- **Segurança funcional:** perfil solicitante não acessa chamados alheios nem comentários internos.
- **Demonstração:** vídeo reproduz um caso completo com dados de exemplo e explica limites conhecidos.

## 8. Riscos prioritários

1. **Escopo excessivo:** liberar MVP de chamados e indicadores antes de acrescentar IA.
2. **Divergência SQL/ORM:** estabelecer baseline de migração antes de introduzir mudanças.
3. **Exposição de segredos:** manter `.env` fora do Git e revisar alterações antes do push.
4. **Resultados não validados:** não declarar banco, testes, deploy ou IA como concluídos sem execução e evidência.

Detalhes, probabilidade e mitigação: [riscos e decisões](riscos-e-decisoes.md).

## 9. Próxima ação concreta

Executar o projeto num computador com Docker Desktop e registrar o resultado do script `scripts/testar-banco.ps1`. Se estiver OK, abrir issues da Sprint 2 para FastAPI, migrações, autenticação e CRUD. Caso o teste falhe, corrigir esquema/Compose antes de avançar.

## 10. Documentos complementares

[Índice geral](../00-indice.md) · [Arquitetura](../arquitetura/arquitetura.md) · [Requisitos](../requisitos/requisitos-e-historias.md) · [Modelo de dados](../banco-de-dados/modelagem.md) · [Contrato de API](../api/contrato-api.md) · [Plano de testes](../testes/plano-de-testes.md) · [Padrões de Git](../contribuicao/git-e-commits.md)

## Documentação UML para a implementação

O escopo tem diagramas **editáveis em PlantUML** de casos de uso, classes, duas sequências, componentes, implantação e estados; [veja a galeria](../uml/README.md). Estes modelos serão usados nas revisões de Sprint 2/3/5 para manter o código alinhado aos requisitos.
