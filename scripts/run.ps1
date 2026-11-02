<#
.SYNOPSIS
    Roda o pipeline localmente no Windows: ingestão, dbt e (opcionalmente) o site.

.EXAMPLE
    .\scripts\run.ps1                   # ingestão + dbt build
    .\scripts\run.ps1 -PularIngestao    # só dbt build (usa o que já está em data/raw)
    .\scripts\run.ps1 -Offline          # ingestão só com os PDFs já baixados em data/pdfs
    .\scripts\run.ps1 -Site             # + gera o site estático em dashboard/build
    .\scripts\run.ps1 -Dev              # + abre o site em modo de desenvolvimento
#>
param(
    [switch]$PularIngestao,
    [switch]$Offline,
    [switch]$Site,
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path $PSScriptRoot -Parent
Set-Location $raiz

# No PowerShell 5.1, um comando externo que falha não para o script sozinho
function Executar {
    param([string]$Comando, [string[]]$Argumentos)
    & $Comando @Argumentos
    if ($LASTEXITCODE -ne 0) { throw "Falhou: $Comando $($Argumentos -join ' ')" }
}

function Etapa([string]$Texto) { Write-Host "`n==> $Texto" -ForegroundColor Cyan }

$python = Join-Path $raiz ".venv\Scripts\python.exe"
$dbt = Join-Path $raiz ".venv\Scripts\dbt.exe"

if (-not (Test-Path $python)) {
    Etapa "Criando o ambiente Python (.venv)"
    Executar "python" @("-m", "venv", ".venv")
}

Etapa "Instalando dependências Python"
Executar $python @("-m", "pip", "install", "-q", "-r", "requirements.txt")

if (-not $PularIngestao) {
    Etapa "Ingestão: relatórios da Fenabrave (a primeira vez baixa ~1 GB de PDFs)"
    $argumentos = @("-m", "ingestao")
    if ($Offline) { $argumentos += "--offline" }
    Executar $python $argumentos
}

Etapa "dbt: modelos e testes"
Push-Location transform
try {
    Executar $dbt @("deps")
    Executar $dbt @("build", "--full-refresh")
} finally {
    Pop-Location
}

if ($Site -or $Dev) {
    Push-Location dashboard
    try {
        if (-not (Test-Path "node_modules")) {
            Etapa "Instalando dependências do site (primeira vez demora alguns minutos)"
            Executar "npm.cmd" @("ci")
        }
        Etapa "Carregando os marts no Evidence"
        Executar "npm.cmd" @("run", "sources")
        if ($Dev) {
            Etapa "Abrindo o site em http://localhost:3000/vendas-veiculos-brasil"
            Executar "npm.cmd" @("run", "dev")
        } else {
            Etapa "Gerando o site estático em dashboard/build"
            Executar "npm.cmd" @("run", "build")
        }
    } finally {
        Pop-Location
    }
}

Etapa "Pronto. Os marts estão em data/marts/"
