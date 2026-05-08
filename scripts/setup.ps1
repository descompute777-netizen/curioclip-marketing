# Agencia de Marketing IA — Setup Script
# Ejecutar desde PowerShell como administrador

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " SETUP: Agencia Marketing IA + Motores" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = "C:\Users\Nick\Desktop\AGENCIA DE MARKETING"

# 1. Verificar Python
Write-Host "`n[1/5] Verificando Python..." -ForegroundColor Yellow
$pyVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python no encontrado. Instalar Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: $pyVersion" -ForegroundColor Green

# 2. Crear entorno virtual
Write-Host "`n[2/5] Creando entorno virtual..." -ForegroundColor Yellow
$venvPath = Join-Path $projectRoot "venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
    Write-Host "  OK: venv creado" -ForegroundColor Green
} else {
    Write-Host "  OK: venv ya existe" -ForegroundColor Green
}

# 3. Instalar dependencias
Write-Host "`n[3/5] Instalando dependencias..." -ForegroundColor Yellow
& "$venvPath\Scripts\pip.exe" install --quiet requests 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK: requests instalado" -ForegroundColor Green
} else {
    Write-Host "  WARN: fallo instalando requests. Instalar manualmente." -ForegroundColor Yellow
}
Write-Host "  INFO: TRIBE v2 NO se instala (licencia NC incompatible)" -ForegroundColor Cyan
Write-Host "  INFO: Prediccion visual reemplazada por VisualEyes (gratis) + heuristico local" -ForegroundColor Cyan

# 4. Clonar MiroFish
Write-Host "`n[4/5] Configurando MiroFish..." -ForegroundColor Yellow
$vendorDir = Join-Path $projectRoot "vendor"
$mirofishDir = Join-Path $vendorDir "MiroFish"
if (-not (Test-Path $mirofishDir)) {
    New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null
    git clone https://github.com/666ghj/MiroFish.git $mirofishDir 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK: MiroFish clonado" -ForegroundColor Green
    } else {
        Write-Host "  WARN: git clone falló. Clonar manualmente." -ForegroundColor Yellow
    }
} else {
    Write-Host "  OK: MiroFish ya existe" -ForegroundColor Green
}

# 5. Verificar estructura
Write-Host "`n[5/5] Verificando estructura..." -ForegroundColor Yellow
$required = @(
    "src\scoring\vscore_engine.py",
    "src\mcp_servers\tribe_v2_server.py",
    "src\mcp_servers\mirofish_server.py",
    "config\settings.json",
    "obsidian_vault\90_MOCs\MOC_Master.md"
)
$allOk = $true
foreach ($f in $required) {
    $path = Join-Path $projectRoot $f
    if (Test-Path $path) {
        Write-Host "  OK: $f" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $f" -ForegroundColor Red
        $allOk = $false
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
if ($allOk) {
    Write-Host " SETUP COMPLETO" -ForegroundColor Green
} else {
    Write-Host " SETUP PARCIAL — revisar archivos faltantes" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nPROXIMOS PASOS:" -ForegroundColor White
Write-Host "  1. Editar config/settings.json con tus placeholders" -ForegroundColor White
Write-Host "  2. Ejecutar: python src/scoring/vscore_engine.py (test)" -ForegroundColor White
Write-Host "  3. Configurar API keys para MiroFish LLM backend" -ForegroundColor White
