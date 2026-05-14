#!/usr/bin/env bash
# CurioClip — Agent Teams Launcher (tmux via MSYS2/Git Bash)
# Uso: bash launch_agents.sh
# Requiere: tmux instalado (pacman -S tmux en MSYS2, o via Git Bash)
#
# Layout 5 panes:
# ┌──────────────────────┬───────────────────────┐
# │ [1] outlier-hunter   │ [2] viral-strategist  │
# ├──────────────────────┼───────────────────────┤
# │ [3] analytics-sci    │ [4] clip-miner        │
# ├──────────────────────┴───────────────────────┤
# │ [5] A0 Director / Cloud Setup / Git          │
# └───────────────────────────────────────────────┘

SESSION="curioclip"
PROJECT="/c/Users/Nick/Desktop/AGENCIA DE MARKETING"

# Matar sesion existente si existe
tmux kill-session -t "$SESSION" 2>/dev/null || true

# Crear nueva sesion (detached)
tmux new-session -d -s "$SESSION" -x 220 -y 50

# Renombrar ventana principal
tmux rename-window -t "$SESSION:0" "agents"

# Pane 1 (ya existe al crear la sesion) — outlier-hunter (top-left)
tmux send-keys -t "$SESSION:0.0" "cd '$PROJECT' && echo '=== [1] OUTLIER-HUNTER — Sprint 2 Outlier Cloning ==='" Enter

# Pane 2 — viral-strategist (top-right, split horizontal del pane 0)
tmux split-window -t "$SESSION:0.0" -h
tmux send-keys -t "$SESSION:0.1" "cd '$PROJECT' && echo '=== [2] VIRAL-STRATEGIST — Hooks + Guiones Sprint 2 ==='" Enter

# Pane 3 — analytics-scientist (bottom-left, split vertical del pane 0)
tmux split-window -t "$SESSION:0.0" -v
tmux send-keys -t "$SESSION:0.2" "cd '$PROJECT' && echo '=== [3] ANALYTICS-SCIENTIST — V-Score V1-V4 ==='" Enter

# Pane 4 — clip-miner (bottom-right, split vertical del pane 1)
tmux split-window -t "$SESSION:0.1" -v
tmux send-keys -t "$SESSION:0.3" "cd '$PROJECT' && echo '=== [4] CLIP-MINER — Produccion V1-V4 ==='" Enter

# Nueva ventana para A0 Director (footer ancho)
tmux new-window -t "$SESSION" -n "director"
tmux send-keys -t "$SESSION:1" "cd '$PROJECT' && echo '=== [5] A0 DIRECTOR / CLOUD SETUP ===' && git status --short" Enter

# Ajustar tamanos (pane 5 ocupa 30% del alto)
tmux select-layout -t "$SESSION:0" tiled

# Ir al pane 1
tmux select-window -t "$SESSION:0"
tmux select-pane -t "$SESSION:0.0"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  CurioClip Agent Teams — tmux session: curioclip ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Adjuntando a la sesion tmux..."
echo "  Ctrl+B → flechas para navegar panes"
echo "  Ctrl+B D para detach (dejar corriendo)"
echo ""
tmux attach-session -t "$SESSION"
