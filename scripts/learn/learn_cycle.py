"""
learn_cycle.py — Orquestador del ciclo completo de aprendizaje M6.

Ejecuta secuencialmente:
  1. Ingest del último snapshot de métricas (ver ingest_metrics_snapshot.py)
  2. Backfill metadata faltante (idempotente)
  3. analyze_patterns.py — re-calcula learn_patterns + calibration_log
  4. generate_insights.py — produce markdown actualizado en 60_Aprendizaje/

Diseñado para correr cada 6h via Windows Task Scheduler, cron, o el
automation_queue del dashboard. Es idempotente — corre 50 veces y nada se
duplica (cada paso re-genera limpio).

Uso manual:
    python scripts/learn/learn_cycle.py
"""
from __future__ import annotations
import sys, subprocess, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run(script_rel: str) -> bool:
    cmd = [sys.executable, str(ROOT / script_rel)]
    print(f"\n>>> {script_rel}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.stdout:
        # solo primeras y últimas 10 lineas (el output largo es del analyze)
        lines = r.stdout.splitlines()
        if len(lines) > 25:
            print("\n".join(lines[:10] + ["    ..."] + lines[-10:]))
        else:
            print(r.stdout)
    if r.returncode != 0:
        print(f"[FAIL] {script_rel} returncode={r.returncode}")
        if r.stderr:
            print(r.stderr[-500:])
        return False
    return True


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    start = datetime.datetime.utcnow()
    print(f"╔══ LEARN CYCLE @ {start.strftime('%Y-%m-%d %H:%M UTC')} ══╗")

    steps = [
        ("scripts/learn/ingest_metrics_snapshot.py",       "Ingest snapshot"),
        ("scripts/learn/backfill_video_metadata.py",       "Backfill metadata"),
        ("scripts/learn/analyze_patterns.py",               "Pattern analysis"),
        ("scripts/learn/generate_insights.py",              "Generate insights"),
        # ─── M6 LEARN — calibración por componente ────────────────────
        ("src/scoring/calibration.py",                      "Simulator calibration (per-component)"),
        ("scripts/learn/generate_calibration_report.py",    "Calibration report"),
        # ─── EVOLUTION ENGINE — cerebro autónomo ──────────────────────
        ("scripts/learn/evolution_engine.py",               "Evolution engine (strategy evolution)"),
    ]
    ok = 0
    for script, name in steps:
        if _run(script):
            ok += 1
            print(f"    ✓ {name}")
        else:
            print(f"    ✗ {name}")

    elapsed = (datetime.datetime.utcnow() - start).total_seconds()
    print(f"\n╚══ {ok}/{len(steps)} steps OK · {elapsed:.0f}s ══╝")
    return 0 if ok == len(steps) else 1


if __name__ == "__main__":
    sys.exit(main())
