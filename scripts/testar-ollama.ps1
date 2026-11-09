# Teste de inferencia do Ollama local com dados ficticios, sem acesso ao banco.
# Uso: powershell -ExecutionPolicy Bypass -File .\scripts\testar-ollama.ps1
param(
    [string]$Model = "qwen2.5:3b",
    [string]$BaseUrl = "http://127.0.0.1:11434"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    $uri = [System.Uri]$BaseUrl
    if ($uri.Scheme -ne "http" -or $uri.Host -notin @("localhost", "127.0.0.1") -or
        $uri.AbsolutePath -ne "/" -or -not [string]::IsNullOrEmpty($uri.Query)) {
        throw "A validacao aceita somente o Ollama local (localhost/127.0.0.1)."
    }

    Write-Host "[1/3] Verificando Ollama em $BaseUrl..."
    $models = Invoke-RestMethod -Uri "$($BaseUrl.TrimEnd('/'))/api/tags" -Method Get -TimeoutSec 15
    $matchingModels = @($models.models | Where-Object { $_.name -eq $Model })
    if ($matchingModels.Count -eq 0) {
        throw "Modelo $Model nao encontrado. Execute: ollama pull $Model"
    }

    Write-Host "[2/3] Testando resposta JSON com pedido sintetico..."
    $payload = @{
        model = $Model
        stream = $false
        format = "json"
        options = @{ temperature = 0; num_predict = 80 }
        messages = @(
            @{
                role = "system"
                content = "Responda somente um objeto JSON com a propriedade ok igual ao booleano true."
            },
            @{
                role = "user"
                content = "Teste local com texto ficticio, sem dados de usuarios nem de chamados."
            }
        )
    } | ConvertTo-Json -Depth 8

    $params = @{
        Uri = "$($BaseUrl.TrimEnd('/'))/api/chat"
        Method = "Post"
        ContentType = "application/json; charset=utf-8"
        Body = [System.Text.Encoding]::UTF8.GetBytes($payload)
        TimeoutSec = 180
    }
    $result = Invoke-RestMethod @params

    if ([string]::IsNullOrWhiteSpace($result.message.content)) {
        throw "Ollama nao retornou texto em message.content."
    }
    $answer = $result.message.content | ConvertFrom-Json -ErrorAction Stop
    if ($answer.ok -ne $true) {
        throw "Resposta JSON invalida para o teste: verifique o modelo e seus logs."
    }

    Write-Host "[3/3] Sucesso: $Model respondeu JSON pelo endpoint local."
    Write-Host "A integracao com a API do PulseOps ainda exige teste manual na interface."
} catch {
    Write-Error "Falha na validacao local: $($_.Exception.Message)"
    exit 1
}
