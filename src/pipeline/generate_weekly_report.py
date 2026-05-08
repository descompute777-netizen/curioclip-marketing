"""
Genera reporte semanal consolidado con KPIs + estado de cada video.
Output: obsidian_vault/50_Analitica/weekly_[fecha].md + actualiza web/data/schedule.json
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta


def main():
    print(f"[WEEKLY] {datetime.now(timezone.utc).isoformat()}")

    today = datetime.now(timezone.utc).date()
    iso_week = today.isocalendar()
    week_id = f"week_{iso_week[1]:02d}_{iso_week[0]}"

    out = Path("obsidian_vault/50_Analitica") / f"weekly_{today.isoformat()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    # Recopilar todos los V-Scores
    sim_dir = Path("obsidian_vault/30_Contenido/simulaciones")
    vscores = list(sim_dir.glob("*_vscore.md"))

    md = f"""---
agente: A0_Director
fecha: {today.isoformat()}
tags: [briefing-semanal, weekly, auto-generado]
week: {week_id}
---

# Briefing Semanal — {today.isoformat()}

## V-Scores recolectados
- Total simulaciones: {len(vscores)}

## Snapshots de analytics
- (Pendiente integración con TikTok API o sync manual desde Chrome Bridge)

## Calibración del predictor
Ver: [[../60_Aprendizaje/calibration_history.json]]

## Próximos pasos

(Auto-generado por GitHub Action — actualizar con datos reales cuando estén disponibles)
"""
    out.write_text(md, encoding="utf-8")
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
