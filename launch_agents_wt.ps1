# CurioClip — Agent Teams Launcher (Windows Terminal)
# Uso: Click derecho > "Ejecutar con PowerShell" o: pwsh -File launch_agents_wt.ps1
#
# Layout:
#   Tab 1 [outlier-hunter]   | Tab 2 [viral-strategist]
#   Tab 3 [analytics-sci]    | Tab 4 [clip-miner / produce]
#   Tab 5 [A0 Director / cloud setup]

$PROJECT = "C:\Users\Nick\Desktop\AGENCIA DE MARKETING"
$PYTHON  = "python"

# Comandos de bienvenida por pane
$OUTLIER_CMD  = "cd '$PROJECT'; Write-Host '=== [1] OUTLIER-HUNTER — Sprint 2 Outlier Cloning ===' -ForegroundColor Cyan; Write-Host 'Listo. Ejecuta el agente desde Claude Code o pega el comando de investigacion.' -ForegroundColor Green"
$VIRAL_CMD    = "cd '$PROJECT'; Write-Host '=== [2] VIRAL-STRATEGIST — Hooks + Guiones Sprint 2 ===' -ForegroundColor Magenta; Write-Host 'Listo. Monitorea outputs en obsidian_vault/10_Estrategia/briefs/' -ForegroundColor Green"
$ANALYTICS_CMD= "cd '$PROJECT'; Write-Host '=== [3] ANALYTICS-SCIENTIST — V-Score V1-V4 + M6 LEARN ===' -ForegroundColor Yellow; Write-Host 'Listo. Outputs: obsidian_vault/30_Contenido/simulaciones/' -ForegroundColor Green"
$CLIPMINER_CMD= "cd '$PROJECT'; Write-Host '=== [4] CLIP-MINER / AUTO-EDITOR — Produccion V1-V4 ===' -ForegroundColor Red; Write-Host 'Para producir: python src/pipeline/produce_all.py' -ForegroundColor Green"
$DIRECTOR_CMD = "cd '$PROJECT'; Write-Host '=== [5] A0 DIRECTOR / CLOUD SETUP / GIT SYNC ===' -ForegroundColor White; Write-Host 'GitHub Actions + vault sync. Git status:' -ForegroundColor Green; git status --short"

# Construir comando wt.exe con 5 panes en 2 tabs
# Tab 1: pane izquierdo (outlier) + split derecho (viral)
# Tab 2: pane izquierdo (analytics) + split derecho (clipminer)
# Tab 3: pane full-width (director)
$wtArgs = @(
    "--title", "CurioClip Agent Teams",
    "new-tab", "--title", "[1] outlier-hunter", "--", "powershell.exe", "-NoExit", "-Command", $OUTLIER_CMD,
    ";", "split-pane", "--vertical", "--title", "[2] viral-strategist", "--", "powershell.exe", "-NoExit", "-Command", $VIRAL_CMD,
    ";", "new-tab", "--title", "[3] analytics-sci", "--", "powershell.exe", "-NoExit", "-Command", $ANALYTICS_CMD,
    ";", "split-pane", "--vertical", "--title", "[4] clip-miner", "--", "powershell.exe", "-NoExit", "-Command", $CLIPMINER_CMD,
    ";", "new-tab", "--title", "[5] A0-Director", "--", "powershell.exe", "-NoExit", "-Command", $DIRECTOR_CMD
)

Write-Host "Abriendo CurioClip Agent Teams en Windows Terminal..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Layout de 3 tabs:" -ForegroundColor White
Write-Host "  Tab 1: [outlier-hunter] | [viral-strategist]" -ForegroundColor Cyan
Write-Host "  Tab 2: [analytics-sci]  | [clip-miner]" -ForegroundColor Yellow
Write-Host "  Tab 3: [A0-Director / cloud / git]" -ForegroundColor Green
Write-Host ""

Start-Process "wt.exe" -ArgumentList $wtArgs

Write-Host "Windows Terminal abierto. Vuelve a Claude Code para ver el progreso de los agentes." -ForegroundColor Green
