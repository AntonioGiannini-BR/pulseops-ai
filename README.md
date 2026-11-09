# PulseOps AI — Gestão Inteligente de Service Desk

Plataforma demonstrativa de gestão de chamados com **React + TypeScript**, **FastAPI**, **PostgreSQL** e triagem supervisionada por IA. Projeto de engenharia de software voltado a portfólio, aprendizagem e validação funcional.

> **Estado:** MVP implementado em branches de desenvolvimento e PRs; CI verifica API, frontend, banco e stack Docker. Um deploy público/empresarial **não** está ativado nem homologado. O modo `mock` usa regras locais; para IA generativa real use Ollama ou API OpenAI configurada.

![Prévia do painel](docs/imagens/dashboard-preview.png)

## Funcionalidades do MVP

- Login por JWT; perfis `admin`, `analista` e `solicitante`; sessão mantida somente em memória no frontend.
- Criação e acompanhamento de chamados, responsável, status, prioridade, comentários públicos/internos e histórico.
- Prazos de SLA, indicadores e distribuição dos chamados; busca/filtros e **exportação CSV dos registros visíveis**.
- **Equipes:** contagens de usuários ativos, analistas e tickets por departamento.
- **Central de IA:** status de provedor e indicadores de sugestões aprovadas, pendentes e rejeitadas.
- **Triagem por IA:** prioridade/categoria/justificativa sugeridas, aplicadas apenas após revisão humana.
- **Assistente de resolução:** hipótese, roteiro de investigação e resposta sugerida por IA.
- **Automações aprovadas:** diagnóstico do banco da própria plataforma, comentário com orientações padronizadas e avanço seguro do fluxo. **Não altera senhas/permissões externas nem executa comandos arbitrários.**
- Auditoria de mudanças e testes automatizados.

## Como rodar no Windows (desenvolvimento)

Pré-requisitos: Docker Desktop com PostgreSQL, Python 3.11+, Node 22+, Git. Para IA real local: [Ollama](https://ollama.com/download/windows) e `ollama pull qwen2.5:3b`.

O projeto usa dois ambientes separados: `.env` na raiz para o PostgreSQL do Docker e `backend/.env` para a API. **Preserve suas configurações existentes**; nunca execute scripts de inicialização sobre um banco em uso.

No primeiro uso, configure uma senha de banco forte em `.env` (baseado em `.env.example`) e inicie apenas o PostgreSQL:

```powershell
docker compose up -d database
```

No arquivo `backend/.env`, defina a URL real do PostgreSQL, uma chave JWT privada e o Ollama:

```dotenv
DATABASE_URL=postgresql+psycopg://USUARIO:SENHA@127.0.0.1:5432/NOME_DO_BANCO
JWT_SECRET_KEY=GERE_E_GUARDE_UM_SEGREDO_ALEATORIO
AI_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

Se não tiver conta ativa, crie um administrador de forma interativa, **sem colocar a senha no terminal como argumento**:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m scripts.create_admin --email admin@exemplo.local --name "Administrador"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Em outro terminal:

```powershell
cd frontend
npm ci
"VITE_API_URL=http://127.0.0.1:8010" | Set-Content .env.local
npm run dev
```

Acesse `http://localhost:5173`. A API de desenvolvimento possui Swagger em `http://127.0.0.1:8010/docs`. No Docker com `APP_ENVIRONMENT=production`, Swagger público fica desabilitado.

Para verificar o Ollama **já instalado no Windows**, antes de conectar o FastAPI, execute na raiz do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\testar-ollama.ps1
```

O script verifica o modelo e uma resposta JSON com um texto fictício, sem executar ações.

## Stack completa em Docker (demonstração privada)

Use `compose.app.yaml` sobre `compose.yaml`: PostgreSQL + FastAPI + Nginx/React, com acesso restrito à máquina local por padrão. Requer `JWT_SECRET_KEY` privado de no mínimo 32 caracteres no `.env` da raiz.

```powershell
docker compose -f compose.yaml -f compose.app.yaml up -d --build --wait
```

Acesse `http://127.0.0.1:8080`. A API usa o prefixo `/api` no proxy Nginx. A inicialização **não recria um volume existente**; nunca use `docker compose down -v` em dados importantes.

O Ollama opcional dentro do Docker exige `--profile local-ai` e baixar o modelo nesse contêiner. O modelo instalado no Windows **não é automaticamente compartilhado com esse contêiner**. Veja os comandos completos, criação segura de conta, teste e backup no [Guia de implantação e release](docs/implantacao/guia-de-release.md).

## Qualidade e documentação

- [Testes e checklist de release](docs/testes/plano-de-testes.md) — inclui Chromium/Playwright e backup/restauração descartável em CI
- [Contrato implementado da API](docs/api/contrato-api.md)
- [Triagem supervisionada](docs/funcionalidades/ia-supervisionada.md)
- [Resolução assistida e automações](docs/funcionalidades/resolucao-assistida.md)
- [Arquitetura, UML e modelagem](docs/00-indice.md)
- [Documentação técnica](DOCUMENTACAO.md), [`llms.txt`](llms.txt) e [`llms-full.txt`](llms-full.txt)

### Limitações antes de uso empresarial

O aplicativo ainda exige hospedagem HTTPS, secrets seguros, backup/restore testado, observabilidade, política de retenção e revisão de segurança independente. A autenticação usa JWT sem revogação central e a IA não acessa sistemas corporativos externos; o deploy em Docker **não é uma homologação de produção**. A sugestão de um LLM não é comprovação de diagnóstico ou correção.
