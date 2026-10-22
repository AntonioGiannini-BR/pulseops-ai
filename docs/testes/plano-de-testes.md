# Estratégia e plano de testes — PulseOps AI

**Separar fatos de metas:** existem scripts SQL de smoke test, mas não há registro de execução do PostgreSQL neste ambiente. Ainda não há FastAPI ou suíte Pytest para executar. O protótipo web é uma demonstração local com dados falsos.

## 1. Níveis de teste planejados

1. **Unitário (futuro):** cálculo SLA, permissões, transições de status, validações e transformação de resposta da IA.
2. **Integração API/banco (futuro):** endpoints + PostgreSQL isolado, integridade entre tickets e histórico, rollback de transação.
3. **Contrato API (futuro):** status HTTP, validação de request/response e paginação conforme OpenAPI.
4. **Frontend (futuro):** formulários, filtros, estados de loading/erro, acessibilidade básica.
5. **End-to-end (futuro):** login → chamado → atribuição → resolução → alteração no painel.
6. **Segurança (futuro):** IDOR, privilégios indevidos, limites e entradas adversariais.

## 2. Casos de teste prioritários

| ID | Caso | Esperado | Etapa |
|---|---|---|---|
| DB-01 | Base nova com seed | 8 tabelas, dados demo, views criadas | Parte 1 |
| DB-02 | Prioridade inválida | Restrição do banco rejeita | Parte 1 |
| DB-03 | Conta fictícia | Seed permanece inativa | Parte 1 |
| API-01 | Criar chamado válido | HTTP 201, solicitante do token, SLA e histórico | Parte 2 |
| API-02 | Campo obrigatório ausente | HTTP 422, nenhum registro criado | Parte 2 |
| AUTH-01 | Solicitante busca chamado alheio | Acesso negado sem dados vazados | Parte 2 |
| AUTH-02 | Solicitante altera prioridade | Acesso negado | Parte 2 |
| SLA-01 | Prioridade alta | Prazo = abertura + 240 min | Parte 2 |
| SLA-02 | Resolução após o prazo | Indicador `fora_do_prazo` | Parte 4 |
| HIS-01 | Alteração de responsável | Evento de histórico com ator | Parte 2 |
| UI-01 | Filtros da tabela | Chamados visíveis correspondem aos filtros | Parte 3 |
| IA-01 | Sugestão pendente | Chamado não é alterado | Parte 5 |
| IA-02 | Retorno da IA inválido/timeout | Erro controlado, triagem manual disponível | Parte 5 |
| SEC-01 | Conteúdo malicioso de comentário | Não executar HTML/script no navegador | Parte 3 |

## 3. Como validar a Parte 1 (Windows/PowerShell)

Na raiz do repositório, com Docker Desktop iniciado:

```powershell
Copy-Item .env.example .env
# Edite POSTGRES_PASSWORD e salve antes de iniciar
notepad .env
docker compose up -d
docker compose ps
.\scripts\testar-banco.ps1
```

Para inspecionar consultas SQL:

```powershell
Get-Content -Raw 'db/queries/indicadores.sql' | docker compose exec -T database sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1'
```

**Atenção:** os SQL em `db/init/` são executados só na primeira criação do volume. `docker compose down -v` apagará todos os dados do banco local: usar somente para reset intencional da demo.

**Registro sugerido de evidência:** data, ambiente (versão Docker/PostgreSQL), comando, resultado, eventual falha e link para issue. Não atualizar este documento para `testado` sem execução.

## 4. Comandos previstos para testes futuros (ainda não disponíveis)

```powershell
# Executar depois que a Parte 2 criar o backend e dependências
cd backend
python -m pytest -q
```

A CI do GitHub Actions será configurada na Parte 6 para bloquear merges com lint/testes falhando. São metas, não verificações atuais.

## 5. Critérios de aprovação de release

- Requisitos P0 demonstrados com dados reais de banco de teste.
- Testes críticos de autorização e persistência passando.
- Nenhuma falha de segurança crítica conhecida sem mitigação.
- Documentação alinhada ao funcionamento atual; limitações explícitas.
- Smoke test reproduzível por outra pessoa, sem credenciais fornecidas pelo autor.
- Fluxo completo demonstrável e falhas de IA tratadas sem comprometer o suporte manual.
