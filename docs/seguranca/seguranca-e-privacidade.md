# Segurança e privacidade — projeto de engenharia

**Status:** controles propostos para as Partes 2–6; **não** declarar o projeto seguro para produção com base apenas neste documento.

## 1. Dados e fronteiras de confiança

O sistema lidará com nomes, e-mails, descrições de chamados, histórico de ações e, futuramente, tokens de sessão. Em demonstrações, usar exclusivamente dados fictícios. Não usar incidentes reais de clientes ou credenciais de terceiros.

**Confianças distintas:** navegador → API → banco; API → provedor de IA. Cada transição exige validação/autorização adequada.

## 2. Matriz de ameaças e controles

| Risco | Controle técnico proposto | Verificação |
|---|---|---|
| Acesso a ticket alheio (IDOR) | Filtro por solicitante no serviço, verificação por objeto | Testes de `403`/`404` |
| Senha comprometida | Hash Argon2id com biblioteca adequada, proteção contra brute force | Teste de login e rate limit |
| Token exposto | Expiração curta, segredo fora do Git, política de armazenamento revisada | Inspeção de cookies/headers/logs |
| SQL injection | Queries parametrizadas via ORM/SQLAlchemy | Casos adversariais de entrada |
| XSS no comentário | Escape padrão do framework, nunca renderizar HTML não confiável | Testes com `<script>` como texto literal |
| Falta de isolamento de funções | Autorização server-side, testes por perfil | Matriz de permissões |
| Vazamento em logs | Redação de senhas, tokens e corpo sensível; logs mínimos | Revisão de log em falha |
| Exposição do PostgreSQL | Binding local em dev; rede privada no deploy | Auditoria da configuração |
| Prompt injection do chamado | Tratar entrada como dados não confiáveis e não dar ferramentas/ações autônomas à IA | Testes de ataques no prompt |
| Saída de IA incorreta | JSON validado, enum fechado, aprovação humana | Casos de resposta inválida |
| API de IA indisponível | Timeout, backoff controlado e fallback manual | Teste de indisponibilidade |

## 3. Autenticação, sessões e controle de acesso

- **Planejado:** hash de senhas usando algoritmo de derivação adequado (Argon2id); nunca criptografia reversível nem hash simples.
- Tokens JWT só serão utilizados após definir expiração, rotação/revogação e forma de armazenamento. Para aplicação web, avaliar cookie `HttpOnly`, `Secure` e `SameSite` e a proteção CSRF correspondente; não tratar JWT como proteção suficiente por si só.
- Rate limit de login, erros genéricos e registro de tentativas suspeitas sem incluir credenciais.
- Aplicar autorização por perfil **e** por vínculo ao objeto; UI não substitui verificação de API.
- Privilégios mínimos para a conta do banco e para a chave da API de IA.

## 4. Segurança de infraestrutura e segredos

- `.env` pertence ao ambiente local e é excluído do Git. `.env.example` só tem nomes de variáveis e placeholders.
- `compose.yaml` da Parte 1 publica PostgreSQL em `127.0.0.1` apenas; ainda não é configuração de produção.
- Não colocar credenciais em commits, imagens, exemplos de documentação ou capturas.
- Antes de deploy: HTTPS, CORS restritivo, backups testados, política de atualização de dependências, limites de request, health check e monitoramento.
- Migrações versionadas e backups antes de alterações destrutivas.

## 5. Privacidade e IA generativa

- Limitar dados pessoais coletados à finalidade de atendimento; estabelecer prazo de retenção e política de exclusão depois de avaliar obrigações aplicáveis.
- Evitar enviar nome, e-mail, senha, IPs privados, tokens ou conteúdo sensível do chamado ao LLM. Minimizar/pseudonimizar antes da chamada.
- Informar no produto quando texto for enviado a um provedor externo e revisar os termos de armazenamento/tratamento desse provedor.
- Registrar modelo utilizado, status de revisão, autor da decisão e timestamp; evitar manter prompts originais com dados sensíveis sem necessidade.
- Preparar avaliação humana de qualidade e vieses de classificações; IA apoia, não toma decisões finais.
- A aderência à LGPD exige análise de finalidade, base legal, transparência, contratos e práticas reais; **esta documentação não comprova conformidade legal**.

## 6. Checklist de segurança antes de publicar a aplicação

- [ ] Autenticação funcionando com senhas protegidas e contas demo desabilitadas.
- [ ] Todas as rotas sensíveis cobertas por testes de permissão.
- [ ] Campos e arquivos limitados em tamanho; upload não está no MVP.
- [ ] Nenhum segredo encontrado em histórico de commits ou variáveis versionadas.
- [ ] HTTPS e cookies/tokens configurados corretamente.
- [ ] CORS e política de origem revisados.
- [ ] Logs não armazenam tokens, senhas, PII desnecessária nem payload bruto de IA.
- [ ] Backups e restauração exercitados.
- [ ] Dependências e imagens atualizadas e verificadas.
- [ ] Integração com IA falha de forma segura e revisão humana obrigatória.
