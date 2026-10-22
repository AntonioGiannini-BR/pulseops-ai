# PulseOps AI — Visão do Produto (Parte 1)

## Problema
Empresas recebem incidentes por e-mail, chat e planilhas, o que dificulta priorização, acompanhamento, medição de atrasos e visão gerencial. Sistemas isolados tornam demoradas as respostas e as análises.

## Proposta de valor

![Interface de demonstração do PulseOps AI](../imagens/dashboard-preview.png)

*Captura do protótipo offline com dados fictícios — não é a aplicação final integrada.*
Uma plataforma web para abertura, encaminhamento, acompanhamento e análise de chamados operacionais, com indicadores e sugestões de IA supervisionadas por pessoas.

## Público-alvo
- **Solicitante:** cria um chamado, consulta andamento, escreve comentários.
- **Analista:** atende chamados, altera status e prioridade de acordo com permissões, registra comentários internos e valida sugestões da IA.
- **Administrador:** gerencia categorias, políticas de SLA, departamentos e perfis de acesso.
- **Gestor (visão futura):** acompanha KPIs agregados, sem necessariamente editar chamados. Na versão 1, a visualização administrativa será usada para isso.

## Metas da primeira versão (MVP)
1. Permitir login seguro e autorização por função.
2. Abrir, listar, filtrar e atualizar chamados.
3. Registrar responsável, solicitante, departamento, categoria, prioridade, datas e histórico de mudanças.
4. Calcular prazos em horas corridas conforme prioridade e marcar SLA vencido.
5. Exibir totais, status, distribuição por prioridade/categoria, taxa de atrasos e tempo médio para resolução.
6. Gerar sugestões de triagem e resumos por IA, sempre com aprovação humana.
7. Expor API REST documentada e disponibilizar aplicação em ambiente de demonstração.

## Fora do escopo do MVP
- Multi-tenant (várias empresas isoladas no mesmo banco).
- Aplicativo móvel nativo.
- Integração real com ERP e sistemas de clientes.
- Escalação automática de incidentes sem supervisão.
- SLA que considera feriados e horário comercial (fase futura).
- Upload de anexos, notificações por e-mail e SSO corporativo (fase futura).

## Indicadores e fórmulas
- **Pendentes:** status aberto, em_triagem ou em_atendimento.
- **Concluídos:** status resolvido ou fechado.
- **Fora do SLA:** pendentes vencidos ou concluídos após `due_at`.
- **Tempo médio de resolução (horas):** média de `resolved_at - opened_at` para chamados resolvidos/fechados.
- **Cumprimento de SLA:** concluídos dentro do prazo / concluídos com prazo definido, em porcentagem.

## Regras de segurança e IA
- Nunca armazenar senha em texto puro; usar hash seguro (Argon2id recomendado).
- A autorização deve ser validada NO BACKEND em toda operação.
- Chamados de exemplo devem usar dados fictícios, sem dados sensíveis.
- Saída do LLM é proposta, não decisão: analista aprova ou rejeita.
- Evitar enviar dados pessoais ou credenciais de chamados para provedores externos de IA.
- Salvar quem aprovou a sugestão, quando aprovou e qual conteúdo foi sugerido.

## Critérios de sucesso de portfólio
- Demonstração reproduzível em máquina nova.
- README com imagens, instruções de instalação e arquitetura.
- Testes automatizados para rotas críticas e regras de negócio.
- Histórico de commits no GitHub com documentação técnica e decisões de projeto.
- Vídeo com o fluxo: registrar problema > analisar > encaminhar > resolver > dashboard.

## Etapas do plano
- **Semana 1:** planejamento + dados + arquitetura + protótipo visual (este pacote).
- **Semana 2:** FastAPI, autenticação e endpoints de chamados.
- **Semana 3:** React/TypeScript e telas consumindo a API.
- **Semana 4:** métricas reais, consultas e relatórios.
- **Semana 5:** integração de IA com revisão humana.
- **Semana 6:** testes, CI, Docker completo, deploy e apresentação.
