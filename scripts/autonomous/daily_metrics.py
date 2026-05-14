"""
Agente Autónomo — Métricas Diarias + M6 LEARN
================================================
Llamado por GitHub Actions (mejorado en analytics.yml) cada 2h.
Lee el estado actual → analytics-scientist analiza → actualiza vault.

Requiere:
  ANTHROPIC_API_KEY
"""
import os
import sys
import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    os.system("pip install anthropic -q")
    import anthropic

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
AGENTS_DIR = ROOT / ".claude" / "agents"


def read_analytics_state() -> str:
    """Lee snapshots de métricas existentes."""
    parts = []

    analitica = VAULT / "50_Analitica"
    if analitica.exists():
        snapshots = sorted(analitica.glob("*.md"))[-5:]
        for s in snapshots:
            parts.append(f"=== {s.name} ===\n" + s.read_text(encoding="utf-8")[:1000])

    vscore_files = list((VAULT / "30_Contenido" / "simulaciones").glob("*vscore*.md")) \
        if (VAULT / "30_Contenido" / "simulaciones").exists() else []
    for v in vscore_files[-3:]:
        parts.append(f"=== {v.name} ===\n" + v.read_text(encoding="utf-8")[:800])

    return "\n\n".join(parts)[:6000]


def main():
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[START] Daily Metrics — {now}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[SKIP] ANTHROPIC_API_KEY no configurada — generando snapshot vacío")
        snapshot_path = VAULT / "50_Analitica" / f"{today}_auto.md"
        snapshot_path.write_text(
            f"---\nfecha: {today}\nagente: auto\nestado: sin_api_key\n---\n\n"
            f"# Snapshot {today}\n\n> ANTHROPIC_API_KEY no configurada en GitHub Secrets.\n"
            f"> Configurar en: github.com/repo/settings/secrets/actions\n",
            encoding="utf-8"
        )
        return

    client = anthropic.Anthropic(api_key=api_key)
    state = read_analytics_state()

    agent_file = AGENTS_DIR / "analytics-scientist.md"
    if agent_file.exists():
        system = agent_file.read_text(encoding="utf-8")
        if "---" in system:
            parts = system.split("---", 2)
            system = parts[2].strip() if len(parts) >= 3 else system
    else:
        system = (
            "Eres el analytics-scientist de CurioClip. Analizas métricas de TikTok/Facebook, "
            "calculas V-Score, calibras el predictor y generas insights accionables."
        )

    prompt = (
        f"Análisis diario — {now}.\n\n"
        f"Estado actual del vault (métricas y V-Scores existentes):\n{state}\n\n"
        f"Genera:\n"
        f"1. Snapshot de métricas del día (con los datos disponibles, indicar si son estimados)\n"
        f"2. Estado de calibración del predictor V-Score\n"
        f"3. Análisis M6 LEARN si hay videos publicados hace 24h o 72h\n"
        f"4. 3 insights accionables para el próximo contenido\n"
        f"5. Alertas si algún KPI está por debajo del target\n\n"
        f"IMPORTANTE: Si no hay datos reales de TikTok API disponibles, "
        f"indicarlo claramente y basar análisis en predicciones V-Score existentes."
    )

    print(f"[API] Llamando analytics-scientist...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.content[0].text

    # Guardar snapshot diario
    snapshot_path = VAULT / "50_Analitica" / f"{today}_auto.md"
    snapshot_path.write_text(
        f"---\nfecha: {today}\nagente: analytics-scientist-cloud\nestado: auto\n---\n\n"
        + content,
        encoding="utf-8"
    )
    print(f"[OK] Snapshot: {snapshot_path}")
    print(f"[DONE] Daily metrics completado.")


if __name__ == "__main__":
    main()
