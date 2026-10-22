# Renderiza diagramas UML a partir dos arquivos .puml no computador local.
# Requisitos: Java + PlantUML JAR, disponivel em https://plantuml.com/download
param(
    [string]$JarPath = ""
)
$ErrorActionPreference = "Stop"
$raiz = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($JarPath)) {
    $JarPath = Join-Path $raiz "tools\plantuml.jar"
}
if (-not (Test-Path $JarPath)) {
    throw "PlantUML nao encontrado em $JarPath. Baixe o JAR oficial e coloque em tools/plantuml.jar ou informe -JarPath."
}
if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
    throw "Java nao encontrado. Instale Java e tente novamente."
}
$arquivos = Get-ChildItem (Join-Path $raiz "docs\uml\diagramas") -Filter "*.puml" -File
if ($arquivos.Count -eq 0) { throw "Nenhum arquivo .puml encontrado." }
foreach ($arquivo in $arquivos) {
    Write-Host "Renderizando $($arquivo.Name)"
    & java -jar $JarPath -charset UTF-8 -tsvg -o ../imagens $arquivo.FullName
    if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar SVG: $($arquivo.Name)" }
    & java -jar $JarPath -charset UTF-8 -tpng -o ../imagens $arquivo.FullName
    if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar PNG: $($arquivo.Name)" }
}
Write-Host "Diagramas gerados em docs\uml\imagens\" -ForegroundColor Green
