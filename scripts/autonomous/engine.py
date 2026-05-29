"""
engine.py — MOTOR ÚNICO DEFINITIVO de CurioClip
================================================================================
Un solo orquestador híbrido que ejecuta el pipeline de 6 módulos con los 10
agentes (A0-A9), donde CADA agente hace trabajo REAL y verificable, y CADA paso
escribe registros a la DB del dashboard (dashboard/curioclip.db). Así la "oficina"
pixel-art y todas las métricas reflejan lo que de verdad está pasando — sin teatro.

Absorbe lo mejor de los 3 sistemas previos:
  - produce_pipeline.py  → PRODUCE con todas las mejoras (compliance, b-roll por
    escena + dedup global, subtítulos whisper, voces ElevenLabs ROTATIVAS, R16,
    quality gate R13).
  - upload_daemon.py     → PUBLISH: registra en upload_schedule.json para que el
    daemon suba vía TikTok Studio (modo actual); flip a API cuando TikTok apruebe.
  - dashboard/db.py      → estado vivo (videos, simulations, automation_queue,
    pipeline_runs, briefings) que alimenta el Mission Control.

Flujo:  A0 abre run → A1 selecciona → [A9 compliance + A2 hook] por guion →
        A4+A8 produce+V-Score → A6 agenda subida → A7 aprende → A0 cierra/briefing.

Uso:
  python scripts/autonomous/engine.py --run obsidian_vault/30_Contenido/guiones_2026-05-29.json
  python scripts/autonomous/engine.py --run guiones.json --limit 2
  python scripts/autonomous/engine.py --register-batch output_pipeline_v2/batch
"""
from __future__ import annotations
import os, sys, json, re
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dashboard import db
from scripts.autonomous.produce_pipeline import (
    produce, compliance_gate, hook_gate, ComplianceError, HookError,
    _load_ledger, _save_ledger,
)
from scripts.autonomous.tts_elevenlabs import VOICE_POOL

ACCOUNT = {"name": "CurioClip", "handle": "fugamental28", "platform": "tiktok",
           "niche": "curiosidades", "color": "#fbbf24"}
SCHEDULE_PATH = ROOT / "output_week_remaining" / "upload_schedule.json"
# 4 horarios LATAM pico (UTC) para repartir la subida del lote
SLOTS_UTC = ["13:00", "16:30", "20:00", "00:30"]


# ─── infraestructura: cuenta + logging de agentes ───────────────────────────
def get_account_id() -> int:
    row = db.query_one("SELECT id FROM accounts WHERE handle=? AND platform=?",
                       (ACCOUNT["handle"], ACCOUNT["platform"]))
    if row:
        return row["id"]
    return db.execute(
        """INSERT INTO accounts (name, handle, platform, niche, color)
           VALUES (?,?,?,?,?)""",
        (ACCOUNT["name"], ACCOUNT["handle"], ACCOUNT["platform"],
         ACCOUNT["niche"], ACCOUNT["color"]))


def agent_run(aid: str, action: str, fn, account_id: int | None = None,
              payload: dict | None = None):
    """Ejecuta una tarea de un agente y la registra REAL en automation_queue
    (in_progress → completed/failed). Esto es lo que ve la oficina pixel-art."""
    qid = db.execute(
        """INSERT INTO automation_queue (agent, action, account_id, payload, status, started_at)
           VALUES (?,?,?,?, 'in_progress', ?)""",
        (aid, action, account_id, db.safe_json(payload) if payload else None, db.now_iso()))
    try:
        result = fn()
        db.execute(
            "UPDATE automation_queue SET status='completed', completed_at=?, result=? WHERE id=?",
            (db.now_iso(), db.safe_json(result), qid))
        return result
    except Exception as e:
        db.execute(
            "UPDATE automation_queue SET status='failed', completed_at=?, result=? WHERE id=?",
            (db.now_iso(), db.safe_json({"error": str(e)}), qid))
        raise


# ─── A8: V-Score REAL (heurístico a partir de señales verídicas del video) ───
_CURIOSITY = ("qué pasaría", "por qué cuando", "prueba esto", "imagina", "nunca",
              "jamás", "secreto", "nadie sabe", "real")

def compute_vscore(script: dict, qa: dict) -> dict:
    """V-Score derivado de atributos REALES (no aleatorio). MiroFish (spread/
    sentiment) queda pendiente hasta tener key Gemini válida → se documenta."""
    hook = (script.get("hook") or "").lower()
    # hook score 0-1: R16 + gatillos de curiosidad + signo de pregunta
    hk = 0.6 + 0.1 * sum(1 for w in _CURIOSITY if w in hook)
    if "?" in hook:
        hk += 0.1
    hk = min(hk, 1.0)
    # atención (proxy VisualEyes 0-10): subtítulos + b-roll único + duración sweet-spot
    checks = qa.get("checks", {})
    ve = 4.0
    ve += 3.0 if checks.get("subtitulos_R11") else 0
    ve += 2.0 if checks.get("broll_unico_R10") else 0
    ve += 1.0 if checks.get("duracion_ok") else 0
    ve = min(ve, 10.0)
    # V-Score parcial (sin MiroFish): renormaliza los pesos disponibles 0.35+0.15
    avail = 0.35 + 0.15
    vscore = (0.35 * (ve / 10) + 0.15 * hk) / avail * 100
    return {"hook_score": round(hk, 3), "ve_attention": round(ve, 2),
            "mirofish_spread": None, "mirofish_sentiment": None,
            "vscore_computed": round(vscore, 1), "source": "heuristic_no_mirofish"}


# ─── PUBLISH (A6): registrar en schedule del daemon (modo actual) ────────────
def _load_schedule() -> list:
    if SCHEDULE_PATH.exists():
        raw = SCHEDULE_PATH.read_bytes()
        raw = raw[3:] if raw[:3] == b"\xef\xbb\xbf" else raw
        try:
            return json.loads(raw)
        except Exception:
            return []
    return []

def schedule_for_upload(video_code: str, title: str, caption: str, final: str,
                        slot_index: int) -> str:
    """Añade el video al upload_schedule.json que consume upload_daemon.py.
    Devuelve el publish_at_utc asignado."""
    sched = _load_schedule()
    day_offset = slot_index // len(SLOTS_UTC)
    hhmm = SLOTS_UTC[slot_index % len(SLOTS_UTC)]
    when = (datetime.utcnow() + timedelta(days=day_offset)).strftime("%Y-%m-%d") + "T" + hhmm + ":00"
    sched = [s for s in sched if s.get("guion_id") != video_code]  # evitar duplicado
    sched.append({"guion_id": video_code, "title": title, "caption": caption,
                  "video_path": final, "publish_at_utc": when, "status": "ready"})
    SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_PATH.write_text(json.dumps(sched, ensure_ascii=False, indent=2), encoding="utf-8")
    return when


# ─── registrar un video producido en la DB del dashboard ─────────────────────
def register_video(account_id: int, script: dict, report: dict, slot_index: int) -> int:
    qa = report.get("qa", {})
    vc = script.get("id")
    final = report.get("final", "")
    status = "produced" if report.get("status") == "LISTO" else "draft"
    # A8: V-Score
    vs = agent_run("A8", "v_score", lambda: compute_vscore(script, qa), account_id,
                   {"video": vc})
    vid = db.execute(
        """INSERT INTO videos (account_id, video_code, guion_id, title, hook, caption,
                               hashtags, niche, file_path, status, vscore_predicted)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (account_id, vc, vc, script.get("caption", vc), script.get("hook"),
         script.get("caption"), " ".join(script.get("hashtags", [])),
         script.get("niche"), final, status, vs["vscore_computed"]))
    db.execute(
        """INSERT INTO simulations (video_id, source, visualeyes_attention,
               mirofish_spread, mirofish_sentiment, hook_score, vscore_computed, raw_json)
           VALUES (?,?,?,?,?,?,?,?)""",
        (vid, vs["source"], vs["ve_attention"], None, None, vs["hook_score"],
         vs["vscore_computed"], db.safe_json({"voice": report.get("voice"), "qa": qa})))
    # A6: agendar subida (solo si pasó quality gate)
    if status == "produced" and final:
        def _sched():
            when = schedule_for_upload(vc, script.get("caption", vc),
                                       script.get("caption", "") + " " +
                                       " ".join(script.get("hashtags", [])), final, slot_index)
            db.execute("UPDATE videos SET status='scheduled', scheduled_at=? WHERE id=?",
                       (when, vid))
            return {"scheduled_at": when, "via": "upload_daemon"}
        agent_run("A6", "schedule_upload", _sched, account_id, {"video": vc})
    return vid


# ─── ORQUESTADOR PRINCIPAL ───────────────────────────────────────────────────
def run_engine(scripts: list[dict], out_root: Path, limit: int | None = None) -> dict:
    db.init_db()
    acc = get_account_id()
    if limit:
        scripts = scripts[:limit]
    run_id = db.execute(
        "INSERT INTO pipeline_runs (run_type, account_id, status) VALUES ('engine_full', ?, 'started')",
        (acc,))
    print(f"\n{'='*64}\nMOTOR ÚNICO CurioClip — run #{run_id} — {len(scripts)} guiones\n{'='*64}")

    # A1 DISCOVER: selección de guiones
    agent_run("A1", "select_scripts", lambda: {"count": len(scripts),
              "ids": [s.get("id") for s in scripts]}, acc)

    used = _load_ledger()
    produced, rejected = [], []
    for i, s in enumerate(scripts):
        vc = s.get("id")
        # A9 + A2 gates (registrados como trabajo real de cada agente)
        try:
            agent_run("A9", "compliance_check", lambda s=s: (compliance_gate(s) or {"verdict": "APROBADO"}), acc, {"video": vc})
            agent_run("A2", "hook_gate_R16", lambda s=s: (hook_gate(s.get("hook", "")) or {"verdict": "OK"}), acc, {"video": vc})
        except (ComplianceError, HookError) as e:
            print(f"  [{vc}] RECHAZADO en gate: {e}")
            rejected.append({"id": vc, "reason": str(e)})
            continue
        # A4 PRODUCE (voz rotativa round-robin → R12)
        vname, voice_id = VOICE_POOL[i % len(VOICE_POOL)]
        try:
            report = agent_run("A4", "produce_video",
                               lambda s=s, v=voice_id: produce(s, out_root / vc, used_ids=used, voice_id=v),
                               acc, {"video": vc, "voice": vname})
        except Exception as e:
            print(f"  [{vc}] ERROR produciendo: {e}")
            rejected.append({"id": vc, "reason": str(e)})
            continue
        vid = register_video(acc, s, report, i)
        produced.append({"id": vc, "db_id": vid, "voice": vname,
                         "status": report.get("status"), "vscore": report.get("qa")})
    _save_ledger(used)

    # A7 LEARN: detectar patrones / calibrar con lo que haya
    def _learn():
        from dashboard.services import scan_patterns, calibrate_predictor
        return {"patterns": scan_patterns(acc), "calibration": calibrate_predictor(acc)}
    learn = agent_run("A7", "learn_cycle", _learn, acc)

    # A0 DIRECTOR: briefing + cerrar run
    ok = sum(1 for p in produced if p["status"] == "LISTO")
    def _brief():
        db.execute(
            """INSERT INTO briefings (sprint_number, date, status_summary, kpis_json, next_steps)
               VALUES (?,?,?,?,?)""",
            (3, db.now_iso(), f"{ok}/{len(scripts)} videos LISTO y agendados",
             db.safe_json({"produced": len(produced), "rejected": len(rejected)}),
             "Subir vía daemon; flip a API al aprobar TikTok"))
        return {"produced": len(produced), "ok": ok, "rejected": len(rejected)}
    brief = agent_run("A0", "briefing", _brief, acc)

    db.execute("UPDATE pipeline_runs SET status='completed', completed_at=?, metadata=? WHERE id=?",
               (db.now_iso(), db.safe_json({"produced": produced, "rejected": rejected,
                "learn": learn}), run_id))
    print(f"\n[MOTOR] run #{run_id} OK · {ok}/{len(scripts)} LISTO · {len(rejected)} rechazados")
    print(f"[MOTOR] dashboard alimentado: videos, simulations, automation_queue, briefings")
    return {"run_id": run_id, "produced": produced, "rejected": rejected, "brief": brief}


def register_existing_batch(batch_dir: Path) -> dict:
    """Registra en la DB videos YA producidos (output_pipeline_v2/batch) sin
    re-producir. Útil para poblar el dashboard con el lote real existente."""
    db.init_db()
    acc = get_account_id()
    reports = []
    bp = batch_dir / "batch_report.json"
    if bp.exists():
        reports = json.loads(bp.read_text(encoding="utf-8"))
    else:  # reconstruir desde report.json por carpeta
        for d in sorted(batch_dir.iterdir()):
            rj = d / "report.json"
            if rj.exists():
                reports.append(json.loads(rj.read_text(encoding="utf-8")))
    guiones = {g["id"]: g for g in json.loads(
        (ROOT / "obsidian_vault" / "30_Contenido" / "guiones_2026-05-29.json").read_text(encoding="utf-8"))}
    run_id = db.execute(
        "INSERT INTO pipeline_runs (run_type, account_id, status) VALUES ('register_batch', ?, 'started')", (acc,))
    n = 0
    for i, rep in enumerate(reports):
        s = guiones.get(rep.get("id"), {"id": rep.get("id"), "caption": rep.get("id"), "niche": rep.get("niche")})
        register_video(acc, s, rep, i)
        n += 1
    db.execute("UPDATE pipeline_runs SET status='completed', completed_at=? WHERE id=?",
               (db.now_iso(), run_id))
    print(f"[MOTOR] registrados {n} videos del lote en la DB del dashboard")
    return {"registered": n, "run_id": run_id}


def main():
    args = sys.argv[1:]
    if "--run" in args:
        sp = Path(args[args.index("--run") + 1])
        scripts = json.loads(sp.read_text(encoding="utf-8"))
        limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
        run_engine(scripts, ROOT / "output_pipeline_v2" / "engine", limit)
    elif "--register-batch" in args:
        register_existing_batch(ROOT / args[args.index("--register-batch") + 1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
