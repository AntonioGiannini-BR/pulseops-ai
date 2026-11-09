# Guia de release e implantação — PulseOps AI

## 1. Escopo e status

A stack está preparada para **demonstração local privada**, não para exposição pública automática. Há backend FastAPI, PostgreSQL e frontend React servido por Nginx em `localhost`. Segurança corporativa, TLS, backup recuperável e testes humanos são requisitos adicionais antes de usar com dados reais.

## 2. Preparar ambiente Windows

Tenha Docker Desktop e Git instalados. Na raiz do repositório:

```powershell
git status
Copy-Item .env.example .env
notepad .env
```

**Se `.env` já existir, não sobrescreva.** O arquivo deve conter `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `JWT_SECRET_KEY`, `APP_PORT` e `AI_PROVIDER`. Gere um `JWT_SECRET_KEY` aleatório com 32+ caracteres. Para gerar uma opção privada em PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copie o resultado **somente** para seu `.env` local. Não compartilhe o segredo no chat, nem faça commit de `.env`. Evite `@`, `:`, `/` e `#` na senha usada no URL do PostgreSQL (ou faça URL-encoding dos caracteres especiais).

## 3. Subir aplicação (sem apagar dados)

```powershell
docker compose -f compose.yaml -f compose.app.yaml config --quiet
docker compose -f compose.yaml -f compose.app.yaml up -d --build --wait
docker compose -f compose.yaml -f compose.app.yaml ps
```

Abra `http://127.0.0.1:8080` (ou a porta `APP_PORT` indicada). Teste:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/api/health
Invoke-RestMethod http://127.0.0.1:8080/api/health/db
```

O proxy roteia `/api/*` para a FastAPI, e o frontend usa URL relativa. O backend não publica porta no host. O PostgreSQL já estava limitado a `127.0.0.1` no arquivo original.

### Criar primeira conta

O seed SQL contém **contas inativas**. Para criar uma conta administrativa própria, sem senha fixa:

```powershell
docker compose -f compose.yaml -f compose.app.yaml exec backend python -m scripts.create_admin --email admin@exemplo.local --name "Administrador"
```

Digite uma senha forte quando o terminal solicitar. O script se recusa a sobrescrever e-mails existentes. Use esse comando apenas na base que você administra.

## 4. IA

O Docker usa `AI_PROVIDER=mock` inicialmente. Isso permite demonstrar o fluxo, **mas não é um LLM**.

Para usar Ollama no próprio Docker:

1. Ajuste `AI_PROVIDER=ollama` e `OLLAMA_BASE_URL=http://ollama:11434` no `.env` da raiz.
2. Inicie com o perfil `local-ai`:
   ```powershell
   docker compose -f compose.yaml -f compose.app.yaml --profile local-ai up -d --build --wait
   ```
3. Baixe o modelo dentro do contêiner (o download feito no Windows não é compartilhado automaticamente):
   ```powershell
   docker compose -f compose.yaml -f compose.app.yaml --profile local-ai exec ollama ollama pull qwen2.5:3b
   ```
4. Confira o dashboard e teste um chamado fictício. Não exponha a porta 11434 à internet.

Se o Ollama já está instalado diretamente no Windows, valide o serviço e a resposta JSON com o script local (na raiz do projeto):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\testar-ollama.ps1
```

O teste usa apenas dados fictícios e não substitui a validação da conexão da API FastAPI com o modelo.

Alternativa para desenvolvimento no Windows: mantenha FastAPI fora do Docker apontando para o Ollama local em `http://127.0.0.1:11434`. API OpenAI é opcional e pode gerar cobrança; a chave fica somente no backend.

## 5. Verificações antes de release

- Verifique que `JWT_SECRET_KEY` é aleatório/privado, que o modo `APP_ENVIRONMENT=production` recusa segredos fracos e que `/api/openapi.json` não está disponível.
- Em `http://127.0.0.1:8080`, teste login, listagem e criação de tickets, filtros/CSV, Equipes, Central de IA e resolução supervisionada.
- Confira `/api/health/db`, registros em `ticket_history` e falhas controladas ao desligar o provedor IA.
- Confirme que a aprovação de automação aparece **antes** da execução e que o comentário público não contém senhas nem dados sensíveis.
- Faça backup de teste e **restaure** em uma base descartável. O CI já testa dump e restore na stack isolada; ainda é necessário validar o procedimento no ambiente de instalação real.

### Backup do PostgreSQL

O comando abaixo produz um dump SQL em arquivo local fora do Git. Ajuste o destino e proteja esse arquivo:

```powershell
docker compose -f compose.yaml -f compose.app.yaml exec -T database sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > pulseops-backup.sql
```

O processo de restauração deve ser validado **somente em banco de teste descartável** antes de qualquer uso com dados importantes. Nunca faça backup em repositório público.

## 6. Encerramento e deploy externo

Pare containers sem apagar volumes:

```powershell
docker compose -f compose.yaml -f compose.app.yaml down
```

**Nunca execute `down -v`** sem intenção explícita de descartar o banco.

O compose publica frontend somente em `127.0.0.1`. Para hospedagem pública, primeiro configure domínio, proxy HTTPS/TLS, secrets no provedor, storage persistente gerenciado, backups automáticos, monitoramento, proteção de autenticação, licenças e política de privacidade. **Nenhum deploy externo foi realizado por este guia.** A aplicação não deve ser apresentada como pronta para uso corporativo antes de cumprir essas condições.

## 7. Ordem de PRs

- PR #23: provedor Ollama e visibilidade do modelo.
- PR #24: planos e automações aprovadas.
- PR #25: Equipes, Central de IA, CSV, stack Docker, bootstrap, testes e documentação.

Integrar na ordem **#23 → #24 → #25** após revisão e testes locais. Não publicar a `main` automaticamente nem apagar o histórico do Git.
