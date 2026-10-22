# Execute na raiz do projeto com PowerShell e Docker Desktop ligados.
$ErrorActionPreference = 'Stop'
if (-not (Test-Path '.env')) { throw 'Arquivo .env ausente. Copie .env.example para .env e configure a senha.' }
Write-Host 'Verificando a conexão com o PostgreSQL...'
docker compose exec -T database sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "SELECT * FROM v_dashboard_kpis;"'
if ($LASTEXITCODE -ne 0) { throw 'Erro ao consultar indicadores.' }
Write-Host 'Executando testes SQL...'
Get-Content -Raw 'db/tests/01_smoke_tests.sql' | docker compose exec -T database sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1'
if ($LASTEXITCODE -ne 0) { throw 'Falha nos testes SQL.' }
Write-Host 'Todos os testes da Parte 1 passaram.' -ForegroundColor Green
