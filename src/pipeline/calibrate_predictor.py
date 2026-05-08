"""
Calibrador del V-Score Predictor.
Compara predicciones (simulaciones) vs métricas reales y ajusta pesos.

Corre cada 2h vía GitHub Action.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
from pathlib import Path
from datetime import datetime, timezone

VAULT = Path("obsidian_vault")
SIM_DIR = VAULT / "30_Contenido" / "simulaciones"
ANALYTICS_DIR = VAULT / "50_Analitica"
CALIBRATION_FILE = VAULT / "60_Aprendizaje" / "calibration_history.json"
CONFIG_FILE = Path("config/settings.json")


def load_history():
    if CALIBRATION_FILE.exists():
        return json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
    return {"runs": [], "weights_history": [], "current_weights": None}


def save_history(h):
    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_FILE.write_text(json.dumps(h, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    print(f"[CALIBRATE] {datetime.now(timezone.utc).isoformat()}")

    history = load_history()

    # Buscar todos los reports de simulación
    sim_reports = list(SIM_DIR.glob("*_report.md"))
    print(f"[INFO] {len(sim_reports)} simulación reports encontrados")

    # Buscar snapshots reales (ej: real_metrics_V5.json)
    real_files = list(ANALYTICS_DIR.glob("real_metrics_*.json"))
    print(f"[INFO] {len(real_files)} snapshots reales encontrados")

    # Si no hay datos reales todavía, solo registrar el run
    if not real_files:
        history["runs"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "no_real_data_yet",
            "n_simulations": len(sim_reports),
            "note": "Esperando primeros snapshots reales de TikTok analytics."
        })
        save_history(history)
        print("[OK] No hay datos reales aún para calibrar. Run logged.")
        return

    # Calcular error medio
    errors = []
    for real_file in real_files:
        try:
            real = json.loads(real_file.read_text(encoding="utf-8"))
            video_id = real.get("video_id")
            # Buscar simulación correspondiente
            sim_file = SIM_DIR / f"personas_rich_{video_id}.json"
            if not sim_file.exists():
                sim_file = SIM_DIR / f"{video_id}_audience_graph.json"
            if not sim_file.exists():
                continue
            sim = json.loads(sim_file.read_text(encoding="utf-8"))

            # Comparar hook rate, save rate, like rate
            real_hook = real.get("hook_rate", 0)
            sim_hook = sim.get("predicted_hook_rate", 0)
            error_hook = abs(real_hook - sim_hook)
            errors.append({
                "video_id": video_id,
                "error_hook": error_hook,
                "real_hook": real_hook,
                "predicted_hook": sim_hook,
            })
        except Exception as e:
            print(f"  [WARN] {real_file.name}: {e}")

    if errors:
        avg_error = sum(e["error_hook"] for e in errors) / len(errors)
        print(f"[CALIBRATE] Error medio hook: {avg_error:.2f}%")

        # Si error >15%, propone ajuste
        if avg_error > 15:
            print(f"[ALERT] Error medio supera 15% — ajuste sugerido a pesos del V-Score")

        history["runs"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "calibrated",
            "avg_error_hook": avg_error,
            "n_videos": len(errors),
            "details": errors,
        })
    else:
        history["runs"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "no_match_sim_real",
            "n_real": len(real_files),
            "n_sim": len(sim_reports),
        })

    save_history(history)
    print("[OK] Calibration history actualizada")


if __name__ == "__main__":
    main()
