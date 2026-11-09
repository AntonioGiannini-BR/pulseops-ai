# Triagem assistida com revisão humana (US-08)

A etapa seguinte está em [Assistente de resolução e automações aprovadas](resolucao-assistida.md).

## Situação

O módulo de triagem permite que um **analista ou administrador** solicite uma sugestão para um chamado aberto, veja a prioridade/categoria recomendadas, o resumo e a justificativa, e decida aprovar ou rejeitar. **Nenhuma sugestão altera um chamado automaticamente.**

O banco `ai_suggestions` já existe no esquema inicial; este módulo não exige uma nova tabela nem executar `db/init/01_schema.sql` novamente.

## Modos de operação

| Modo | Variáveis no `backend/.env` | Comportamento |
|---|---|---|
| Demonstração (padrão) | `AI_PROVIDER=mock` | Heurística local determinística por palavras-chave; **não é um modelo de IA** |
| Modelo externo | `AI_PROVIDER=openai`, `OPENAI_API_KEY=...`, `AI_MODEL=gpt-4o-mini` | Requisição ao provedor configurado; necessita rede e chave válida |
| Modelo local (Ollama) | `AI_PROVIDER=ollama`, `OLLAMA_MODEL=qwen2.5:3b` | Gera propostas com um LLM local na porta 11434; não exige chave de API nem envia dados à OpenAI |

`AI_TIMEOUT_SECONDS=10` limita a espera do provedor externo (2 a 30 segundos); `OLLAMA_TIMEOUT_SECONDS=120` limita a espera local (10 a 300 segundos). A chave fica **somente no backend** e não deve ser adicionada ao Git nem a variáveis `VITE_*`.

O modo OpenAI usa a API de Chat Completions com resposta JSON e validação de esquema. O nome do modelo é configurável. Antes de habilitar a API externa, confirme permissões de uso, custos e política de dados da sua organização.

## Endpoints

Todos exigem JWT e perfil `admin` ou `analista`.

- `GET /tickets/{ticket_id}/ai-suggestions` — lista sugestões e decisões anteriores.
- `POST /tickets/{ticket_id}/ai-suggestions` — solicita e persiste uma sugestão `pendente` (HTTP 201).
- `POST /tickets/{ticket_id}/ai-suggestions/{suggestion_id}/review` — recebe `{"decision":"aprovada"}` ou `{"decision":"rejeitada"}`.

O botão **Gerar sugestão** faz uma chamada explícita. Uma nova sugestão não pode ser gerada enquanto houver outra pendente no mesmo chamado (HTTP 409). Chamados resolvidos/fechados não recebem novas sugestões nem aprovação, mas podem ter uma sugestão rejeitada.

**Ao aprovar:** prioridade e categoria são atualizadas em uma transação junto à revisão e à auditoria. Se a prioridade mudar, `due_at` é recalculado com `sla_policies`, desde `opened_at`. Ao rejeitar, o chamado permanece intacto. Repetir uma revisão retorna HTTP 409.

## Privacidade e falhas

- Apenas título e até 1.500 caracteres da descrição, categoria atual e categorias permitidas são enviados ao modelo selecionado (local ou externo). Comentários, histórico, identidade do solicitante e JWT **não** são enviados.
- E-mails e sequências numéricas comuns são parcialmente mascarados; isso **não garante anonimização completa**. Use dados fictícios em demonstrações e não envie informações sensíveis sem autorização.
- O texto do chamado é tratado como entrada não confiável; a resposta é validada por tipo, tamanho, prioridade e categoria ativa. A revisão humana continua obrigatória.
- Timeout/falha do provedor retorna HTTP 503; resposta inválida retorna HTTP 502. **Não há fallback silencioso** para sugestões fictícias e o atendimento normal continua funcionando.
- O histórico registra `ai_sugestao_criada`, `ai_sugestao_aprovada` ou `ai_sugestao_rejeitada`, além das alterações reais de prioridade e categoria.

## Testes

O workflow `Backend Tests` executa os testes de integração, inclusive `backend/tests/test_ai_triage.py`, com PostgreSQL isolado no GitHub Actions. O workflow `Frontend Build` valida TypeScript/Vite.

Para testar manualmente, inicie o backend e frontend, entre como analista/admin, abra um chamado em andamento, clique em **Gerar sugestão** e aprove/rejeite. Confira `ticket_history`, `ai_suggestions`, prioridade, categoria e SLA após atualizar a página.

**Limitações atuais:** não há proteção de frequência global, painel de custos, análise de anexos, anonimização garantida nem testes end-to-end em navegador. Para produção, esses pontos e a política de retenção de dados precisam de revisão.

## Verificar o modo ativo sem expor segredos

O endpoint autenticado `GET /ai/status` exige perfil `admin` ou `analista` e retorna somente `provider`, `configured` e `model`. **Nunca** retorna `OPENAI_API_KEY`. A interface mostra claramente se está em demonstração, com modelo externo configurado ou sem chave. Se a chave não estiver configurada, o botão de geração fica indisponível no modo externo.

No modo OpenAI, `configured: true` confirma **somente** a presença da chave na configuração, não sua validade, crédito disponível nem conectividade com a API. No modo Ollama, `configured: true` indica que não é necessária uma chave; **não confirma que o servidor Ollama está em execução**. Uma chamada real pode falhar com HTTP 503; nesses casos, nenhuma sugestão fictícia é criada automaticamente.

## Ativar IA real no Windows (PowerShell)

No VS Code, atualize a branch com a funcionalidade e abra **somente** `backend/.env` (não o `.env` da raiz do Docker):

```powershell
cd C:\Users\Antonio\pulseops-ai\backend
notepad .env
```

Preserve `DATABASE_URL` e `JWT_SECRET_KEY` já configurados. Para habilitar o provedor externo, ajuste estas variáveis **no arquivo local, fora do Git**:

```dotenv
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
AI_TIMEOUT_SECONDS=10
OPENAI_API_KEY=COLOQUE_SUA_CHAVE_AQUI_APENAS_NO_ARQUIVO_LOCAL
```

Reinicie o FastAPI após salvar. Entre como analista/admin, abra um chamado fictício e confira a indicação de modelo externo antes de clicar em **Gerar sugestão**. Não envie sua chave ao chat, não use `VITE_OPENAI_API_KEY` e não compartilhe arquivos `.env`. O uso da API pode gerar custos e envia parte do título/descrição ao provedor. Verifique a política de privacidade e as permissões antes de usar dados reais.

Para voltar ao modo local sem chamadas externas, use `AI_PROVIDER=mock` e reinicie o backend.

## Usar IA generativa local com Ollama (Windows, sem chave paga)

**Requisitos sugeridos:** 16 GB de RAM e espaço livre para baixar o modelo; o desempenho depende da CPU/GPU. O modelo inicial é `qwen2.5:3b`, adequado para começar a testar; as respostas precisam de revisão humana.

1. Instale o [Ollama para Windows](https://ollama.com/download/windows). Alternativamente, no PowerShell: `winget install Ollama.Ollama`. Reinicie o terminal se o comando não for reconhecido.
2. Baixe o modelo (pode levar alguns minutos e consumir espaço em disco):

   ```powershell
   ollama pull qwen2.5:3b
   ollama list
   ```

3. Mantenha o aplicativo Ollama aberto. No Windows, ele normalmente inicia o serviço local automaticamente. Se não estiver iniciado, execute `ollama serve` em outro terminal (não execute uma segunda instância se a porta 11434 já estiver em uso).
4. Em **`backend/.env`**, mantenha o `DATABASE_URL` e `JWT_SECRET_KEY` existentes e configure:

   ```dotenv
   AI_PROVIDER=ollama
   OLLAMA_MODEL=qwen2.5:3b
   OLLAMA_TIMEOUT_SECONDS=120
   ```

5. Reinicie o FastAPI, atualize o frontend e abra um chamado fictício. O painel deve mostrar **IA local selecionada (qwen2.5:3b)**. Clique em **Gerar sugestão** após revisar/rejeitar qualquer sugestão pendente. Uma resposta bem-sucedida terá `model_name=ollama/qwen2.5:3b`, prioridade, categoria, resumo e justificativa.

O backend conversa **somente** com `http://127.0.0.1:11434/api/chat` quando `AI_PROVIDER=ollama`; não é necessário expor o serviço Ollama à rede ou colocar uma chave no frontend. O endpoint `GET /ai/status` não verifica a conectividade local. Se o Ollama estiver desligado, o modelo não estiver instalado ou a chamada exceder o tempo limite, a API retorna HTTP 503 sem criar sugestão fictícia.

Para voltar ao modo de demonstração, configure `AI_PROVIDER=mock` e reinicie o backend. **Não execute os scripts de inicialização do banco novamente** apenas para trocar de provedor.

O Ollama processa localmente os dados enviados ao modelo, mas os chamados ainda ficam armazenados no PostgreSQL. Evite dados sensíveis em testes e não exponha a porta 11434 à internet.
