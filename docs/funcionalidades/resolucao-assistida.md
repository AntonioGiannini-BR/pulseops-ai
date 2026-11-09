# Assistente de resolução e automações aprovadas

## Implementação

O PulseOps AI agora oferece dois recursos complementares para analistas e administradores:

1. **Plano de resolução com IA:** gera uma hipótese inicial, passos de diagnóstico, como verificar a correção e uma resposta sugerida. A saída é apenas texto para revisão humana; **nenhum passo é executado pelo modelo**.
2. **Automações controladas:** ações implementadas pelo backend, com prévia, confirmação explícita do usuário, checagem de estado, controle de acesso e auditoria. Não são geradas nem parametrizadas pelo LLM.

### Automações permitidas

| ID | Ação | Efeito real | Restrições |
|---|---|---|---|
| `diagnose_platform` | Verificar saúde da plataforma | Executa `SELECT 1` no PostgreSQL da aplicação e registra o resultado no histórico | Não diagnostica o portal, rede ou servidor citado pelo solicitante |
| `send_guidance` | Enviar orientações | Publica um comentário **público** com texto padronizado conforme a categoria do chamado | Não envia senhas, não altera contas; bloqueia reenvio pela mesma automação |
| `advance_workflow` | Avançar etapa | Altera `aberto → em_triagem` ou `em_triagem → em_atendimento`, registrando histórico | Não resolve nem fecha chamados; respeita a etapa atual |

As instruções públicas são **templates do servidor**, não mensagens geradas pelo modelo. Para responder com o texto sugerido pelo LLM, o analista deve revisá-lo e usar manualmente a funcionalidade de comentários já existente.

## API

Todas as rotas exigem JWT e perfil `admin` ou `analista`:

- `GET /tickets/{ticket_id}/resolution-automations`: retorna `expected_status` e lista de ações com `id`, `label`, `description`, `preview`, `available` e `reason`.
- `POST /tickets/{ticket_id}/resolution-guide`: retorna `model_name` e `guide` com `probable_cause`, `steps`, `verification`, `requester_reply`. Não persiste nem altera o chamado.
- `POST /tickets/{ticket_id}/resolution-automations/{action_id}/execute`: exige corpo JSON com `{"approved":true,"expected_status":"aberto"}` (ajuste o status ao valor retornado na prévia). Executa uma única ação permitida.

A confirmação não é implícita: `approved` deve ser literalmente `true`. Status desatualizado, ação indisponível ou tentativa de repetir o envio de orientações retornam HTTP 409; corpo inválido/ação não permitida, HTTP 422; usuário sem permissão, HTTP 401/403.

O backend trava a linha do chamado durante a ação e grava mutação + histórico na mesma transação. As ações ficam registradas como `automacao_diagnostico`, `automacao_orientacao` ou `automacao_fluxo`; a transição também registra `mudanca_status`. O comentário público aparece na seção de comentários e pode ser visto pelo solicitante.

## IA local com Ollama

Se o `backend/.env` estiver com `AI_PROVIDER=ollama` e `OLLAMA_MODEL=qwen2.5:3b`, o plano é gerado pelo modelo local já instalado. O plano é validado por esquema e limites de tamanho; falhas de conexão retornam 503 e respostas inválidas retornam 502. No modo `mock`, o sistema mostra um guia demonstrativo, claramente identificado como tal.

O texto do chamado é parcialmente minimizado (por exemplo, e-mails comuns), mas **isso não garante anonimização**. Não use dados sensíveis em demonstrações sem autorização.

## Como testar no Windows

1. Mantenha Ollama, FastAPI, React e PostgreSQL ativos.
2. Na branch `feat/assisted-resolution-automations`, atualize o código e reinicie o FastAPI.
3. Abra um chamado fictício como analista/admin e encontre **Assistente de resolução**.
4. Clique em **Gerar plano com IA**. Confira a hipótese, os passos, a verificação e a resposta sugerida.
5. Em **Automações disponíveis**, leia a prévia e clique em **Revisar e executar**. Confirme no diálogo. Para a ação de orientações, observe o novo comentário público; para avanço de fluxo, observe a mudança de status.
6. Confira o histórico do chamado e teste se a ação de orientações não pode ser repetida.

**Não é necessário recriar o banco nem executar `db/init/01_schema.sql`.**

## Limites e próximos passos

Este MVP **não corrige problemas de autenticação em sistemas externos**, não redefine senhas, não reinicia serviços e não executa shell/SQL arbitrário. Para executar correções reais em sistemas de terceiros, serão necessários conectores com permissões mínimas, políticas por ação, validação de alvos, consentimento explícito, logs e testes de segurança. Nenhuma saída do LLM deve virar comando direto.

A confirmação é feita por ação no painel; o backend exige a flag explícita e verifica a permissão. Para implantação em produção, recomenda-se também proteção contra repetição de requisições, rate limiting, trilha de auditoria imutável, políticas de acesso por ambiente e revisão de conteúdo público.
