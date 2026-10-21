# Requisitos e histórias de usuário

> **Estado da documentação:** Requisitos e critérios de aceite para orientar a implementação; funcionalidades futuras não devem ser descritas como entregues.

## Histórias priorizadas

![Jornada de atendimento de um chamado](../imagens/03-fluxo-chamado.png)
| ID | Perfil | História | Critério de aceite | Prioridade |
|---|---|---|---|---|
| US-01 | Solicitante | Quero abrir um chamado | Título, descrição e categoria obrigatórios; ID gerado no banco | P0 |
| US-02 | Solicitante | Quero listar meus chamados | Listagem filtrada pelo usuário autenticado | P0 |
| US-03 | Analista | Quero ver a fila de atendimento | Filtrar por status, prioridade, categoria e responsável | P0 |
| US-04 | Analista | Quero atualizar status e responsável | Mudança autorizada; histórico registrado | P0 |
| US-05 | Admin | Quero gerenciar prioridade e prazo | Política de SLA aplicada ao criar/alterar prioridade | P1 |
| US-06 | Analista | Quero comentar em chamados | Comentário guarda autor e data; interno não aparece a solicitantes | P1 |
| US-07 | Admin | Quero ver painel de indicadores | KPIs calculados com dados reais do banco | P1 |
| US-08 | Analista | Quero sugestão de triagem pela IA | Sugestão mostrada como pendente e nunca aplicada sem aprovação | P2 |
| US-09 | Admin | Quero relatório exportável | Download CSV com filtros ativos | P2 |

## Requisitos não funcionais
- **RNF-01 Segurança:** validações no servidor, senhas em hash, autorização por perfil, segredo fora do Git.
- **RNF-02 Performance:** paginação na listagem; índices em campos pesquisados com frequência.
- **RNF-03 Qualidade:** testes de regras de negócio e execução automatizada na CI.
- **RNF-04 Observabilidade:** logs de erro sem senhas/tokens e histórico de ações de chamados.
- **RNF-05 Confiabilidade:** persistência PostgreSQL com backups na etapa de implantação.
- **RNF-06 Usabilidade:** interface responsiva, contraste adequado, estados de erro e sucesso acessíveis.
- **RNF-07 Privacidade:** dados fictícios em demos; limitar armazenamento e envio externo de dados.

## Regras funcionais detalhadas
1. Um chamado tem um solicitante, uma categoria, um status e uma prioridade obrigatórios.
2. Uma atribuição para analista é opcional no momento da criação.
3. Um chamado pode receber múltiplos comentários, registros de histórico e sugestões da IA.
4. Chamados resolvidos/fechados devem registrar data de resolução; os fechados também data de fechamento.
5. O SLA inicial considera horas corridas: crítica 1h; alta 4h; média 24h; baixa 72h.
6. Se `resolved_at > due_at`, foi concluído fora do prazo. Se aberto e `NOW() > due_at`, está atrasado.
7. A API calculará `due_at` a partir da política de SLA; o banco mantém `NULL` temporariamente para suportar migrações/legado.
8. Trocas de status, responsável ou prioridade gerarão eventos em `ticket_history` implementados na semana 2.
9. Apenas analistas/admins aprovam sugestões de IA, e isso deve ser registrado com usuário e data.
10. Contas fictícias da seed permanecem desativadas; contas reais serão cadastradas de forma segura.

## Critério de conclusão da Parte 1
- [x] Visão do produto definida.
- [x] Histórias de usuário e limites do MVP definidos.
- [x] Modelo entidade-relacionamento documentado.
- [x] Esquema SQL, índices, checks e chaves estrangeiras escritos.
- [x] Dados demonstrativos e consultas preparadas.
- [x] Docker Compose de banco preparado.
- [x] Protótipo navegável (offline, sem backend) criado.
- [ ] Banco executado e testes integridade confirmados no computador do desenvolvedor.
