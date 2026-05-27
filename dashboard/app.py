"""
CurioClip Mission Control — FastAPI application.

Sections (each a router):
  - / (home) → overview HTML
  - /partial/<section> → HTMX-loaded panels
  - /api/accounts, /api/videos, /api/suggestions, ...
  - /api/learn/* → ciclo autónomo de aprendizaje M6 LEARN (APScheduler cada 6h)
"""
import json
import os
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Local
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from dashboard import db
from dashboard.models import (
    AccountIn, VideoIn, SuggestionIn, MetricsIn, AutomationIn, VideoStatusUpdate,
    FeedbackIn,
)

# ─── M6 LEARN — estado en memoria ───────────────────────────────────────────

_learn_state: dict = {
    "last_run_at": None,
    "last_result": None,
    "next_run_at": None,
    "running": False,
    "runs": 0,
}


def _run_learn_cycle_background() -> dict:
    """Ejecuta el ciclo completo de aprendizaje en background (thread-safe)."""
    if _learn_state["running"]:
        return {"status": "already_running"}
    _learn_state["running"] = True
    _learn_state["last_run_at"] = datetime.utcnow().isoformat()
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "learn" / "learn_cycle.py")],
            capture_output=True, text=True, encoding="utf-8", timeout=600
        )
        summary = {
            "status": "ok" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout_tail": (result.stdout or "")[-3000:],
            "stderr_tail": (result.stderr or "")[-500:],
            "ran_at": _learn_state["last_run_at"],
        }
    except Exception as e:
        summary = {"status": "exception", "error": str(e),
                   "ran_at": _learn_state["last_run_at"]}
    finally:
        _learn_state["running"] = False
        _learn_state["runs"] += 1
        _learn_state["last_result"] = summary
        # Calcular próxima ejecución
        _learn_state["next_run_at"] = (
            datetime.utcnow() + timedelta(hours=6)
        ).isoformat()
    return summary


def _schedule_learn_cycle():
    """Lanza learn_cycle en un daemon thread (no bloquea el servidor)."""
    t = threading.Thread(target=_run_learn_cycle_background, daemon=True)
    t.start()
    return t


# ─── APScheduler setup ──────────────────────────────────────────────────────

def _start_scheduler():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        # Ciclo de aprendizaje cada 6h
        scheduler.add_job(
            _run_learn_cycle_background,
            trigger="interval",
            hours=6,
            id="learn_cycle",
            replace_existing=True,
            max_instances=1,
            name="M6 LEARN — ciclo autónomo",
        )
        scheduler.start()
        # Calculamos cuándo será la primera ejecución
        job = scheduler.get_job("learn_cycle")
        if job and job.next_run_time:
            _learn_state["next_run_at"] = job.next_run_time.isoformat()
        print(f"[SCHEDULER] M6 LEARN arrancado · primer ciclo en 6h · "
              f"next={_learn_state['next_run_at']}")
        return scheduler
    except Exception as e:
        print(f"[WARN] APScheduler no disponible: {e} — ciclo manual via /api/learn/cycle")
        return None


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app_: FastAPI):
    # Startup
    scheduler = _start_scheduler()
    yield
    # Shutdown
    if scheduler:
        scheduler.shutdown(wait=False)


# ─── App init ───────────────────────────────────────────────────────────────

app = FastAPI(title="CurioClip Mission Control", version="1.0.0",
              lifespan=lifespan)

templates = Jinja2Templates(directory=str(HERE / "templates"))
templates.env.filters["money"] = lambda v: f"{v:,}".replace(",", ".")
templates.env.filters["pct"] = lambda v: f"{(v or 0)*100:.1f}%"
templates.env.filters["short"] = lambda v, n=80: (v[:n] + "...") if v and len(v) > n else (v or "")
templates.env.filters["fromjson"] = lambda v: json.loads(v) if v else {}
templates.env.filters["abs"] = abs

app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")

db.init_db()


# ─── Helpers ────────────────────────────────────────────────────────────────

def _ctx(request: Request, **extra) -> dict:
    return {"request": request, "now": datetime.utcnow(), **extra}


def _all_accounts() -> list[dict]:
    return db.query("SELECT * FROM accounts ORDER BY status, name")


# ═════════════════════════════════════════════════════════════════════════════
# PAGES
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    stats = db.stats_overview()
    recent_videos = db.query(
        """SELECT v.*, a.name as account_name, a.color as account_color
           FROM videos v JOIN accounts a ON a.id=v.account_id
           ORDER BY COALESCE(v.published_at, v.created_at) DESC LIMIT 8"""
    )
    next_24h = db.query(
        """SELECT v.*, a.name as account_name FROM videos v
           JOIN accounts a ON a.id=v.account_id
           WHERE v.scheduled_at IS NOT NULL
             AND v.scheduled_at > datetime('now')
             AND v.scheduled_at < datetime('now', '+24 hours')
           ORDER BY v.scheduled_at"""
    )
    return templates.TemplateResponse(
        "index.html",
        _ctx(request, stats=stats, accounts=_all_accounts(),
             recent_videos=recent_videos, next_24h=next_24h, section="overview"),
    )


@app.get("/partial/{section}", response_class=HTMLResponse)
def partial(request: Request, section: str):
    """HTMX-loaded section panels."""
    valid = {
        "overview", "cuentas", "calendario", "pipeline", "simulaciones",
        "crecimiento", "sugerencias", "automatizacion", "aprendizaje", "briefings",
        "oficina", "feedback",
    }
    if section not in valid:
        raise HTTPException(404, "Unknown section")
    ctx = _ctx(request, accounts=_all_accounts(), section=section)

    if section == "overview":
        ctx["stats"] = db.stats_overview()
        ctx["recent_videos"] = db.query(
            """SELECT v.*, a.name as account_name, a.color as account_color
               FROM videos v JOIN accounts a ON a.id=v.account_id
               ORDER BY COALESCE(v.published_at, v.created_at) DESC LIMIT 8"""
        )
        ctx["next_24h"] = db.query(
            """SELECT v.*, a.name as account_name FROM videos v
               JOIN accounts a ON a.id=v.account_id
               WHERE v.scheduled_at IS NOT NULL
                 AND v.scheduled_at > datetime('now')
                 AND v.scheduled_at < datetime('now', '+24 hours')
               ORDER BY v.scheduled_at"""
        )

    elif section == "cuentas":
        rows = []
        for a in _all_accounts():
            extra = db.query_one(
                """SELECT COUNT(*) as videos_count,
                          SUM(CASE WHEN status='published' THEN 1 ELSE 0 END) as published_count
                   FROM videos WHERE account_id=?""", (a["id"],)
            ) or {}
            a.update(extra)
            rows.append(a)
        ctx["accounts_rich"] = rows

    elif section == "calendario":
        # Provide JSON events feed inline for FullCalendar
        ctx["events_url"] = "/api/calendar/events"

    elif section == "pipeline":
        stages = ["draft", "in_production", "produced", "scheduled", "published", "archived"]
        ctx["stages"] = stages
        ctx["pipeline"] = {
            s: db.query(
                """SELECT v.*, a.name as account_name, a.color as account_color
                   FROM videos v JOIN accounts a ON a.id=v.account_id
                   WHERE v.status=? ORDER BY v.updated_or_created LIMIT 20""".replace(
                    "v.updated_or_created", "COALESCE(v.scheduled_at, v.created_at) DESC"
                ),
                (s,),
            )
            for s in stages
        }

    elif section == "simulaciones":
        ctx["sims"] = db.query(
            """SELECT v.id, v.title, v.video_code, v.vscore_predicted, v.vscore_actual,
                      a.name as account_name, a.color as account_color
               FROM videos v JOIN accounts a ON a.id=v.account_id
               WHERE v.vscore_predicted IS NOT NULL
               ORDER BY v.published_at DESC NULLS LAST LIMIT 50"""
        )
        ctx["calibration"] = db.query(
            "SELECT * FROM calibration_log ORDER BY computed_at DESC LIMIT 10"
        )

    elif section == "crecimiento":
        ctx["growth_url"] = "/api/growth/data"

    elif section == "sugerencias":
        ctx["suggestions"] = db.query(
            "SELECT * FROM suggestions ORDER BY status, added_at DESC LIMIT 100"
        )

    elif section == "automatizacion":
        ctx["queue"] = db.query(
            """SELECT q.*, a.name as account_name FROM automation_queue q
               LEFT JOIN accounts a ON a.id=q.account_id
               ORDER BY
                 CASE q.status WHEN 'in_progress' THEN 0 WHEN 'pending' THEN 1 ELSE 2 END,
                 q.scheduled_for ASC NULLS LAST LIMIT 50"""
        )
        ctx["runs"] = db.query(
            "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 10"
        )

    elif section == "aprendizaje":
        ctx["calibration"] = db.query(
            "SELECT * FROM calibration_log ORDER BY computed_at DESC LIMIT 15"
        )
        ctx["patterns"] = db.query(
            """SELECT p.*, a.name as account_name FROM learn_patterns p
               LEFT JOIN accounts a ON a.id=p.account_id
               ORDER BY avg_views DESC LIMIT 30"""
        )
        ctx["svr_rows"] = db.query(
            """SELECT s.*, v.video_code, v.niche
               FROM simulations_vs_reality s
               JOIN videos v ON v.id = s.video_id
               ORDER BY ABS(s.vscore_predicted_total - s.vscore_real_total) DESC
               LIMIT 20"""
        )
        ctx["weight_history"] = db.query(
            "SELECT * FROM vscore_weight_history ORDER BY version DESC LIMIT 10"
        )

    elif section == "briefings":
        ctx["briefings"] = db.query(
            "SELECT * FROM briefings ORDER BY date DESC LIMIT 12"
        )

    elif section == "feedback":
        ctx["feedback_items"] = db.query(
            "SELECT * FROM user_feedback ORDER BY "
            "CASE status WHEN 'pendiente' THEN 0 WHEN 'leido' THEN 1 "
            "WHEN 'en_progreso' THEN 2 ELSE 3 END, created_at DESC LIMIT 100"
        )
        ctx["feedback_stats"] = {
            "pendiente": len([f for f in ctx["feedback_items"] if f["status"] == "pendiente"]),
            "resuelto": len([f for f in ctx["feedback_items"] if f["status"] == "resuelto"]),
            "total": len(ctx["feedback_items"]),
        }

    elif section == "oficina":
        # No DB context needed — game polls /api/oficina/state on its own.
        pass

    return templates.TemplateResponse(f"partials/{section}.html", ctx)


# ═════════════════════════════════════════════════════════════════════════════
# API — ACCOUNTS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/accounts")
def api_accounts():
    return _all_accounts()


@app.post("/api/accounts")
def api_account_create(body: AccountIn):
    rid = db.execute(
        """INSERT INTO accounts (name, handle, platform, niche, followers_current,
                                 followers_goal, color, notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (body.name, body.handle, body.platform, body.niche, body.followers_current,
         body.followers_goal, body.color, body.notes),
    )
    return {"id": rid}


@app.delete("/api/accounts/{aid}")
def api_account_delete(aid: int):
    for table in ("automation_queue", "pipeline_runs", "learn_patterns", "calibration_log"):
        db.execute(f"UPDATE {table} SET account_id=NULL WHERE account_id=?", (aid,))
    db.execute("DELETE FROM account_metrics_daily WHERE account_id=?", (aid,))
    db.execute("DELETE FROM accounts WHERE id=?", (aid,))
    return {"ok": True}


# ═════════════════════════════════════════════════════════════════════════════
# API — VIDEOS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/videos")
def api_videos(account_id: Optional[int] = None, status: Optional[str] = None):
    where, params = [], []
    if account_id:
        where.append("v.account_id = ?")
        params.append(account_id)
    if status:
        where.append("v.status = ?")
        params.append(status)
    sql = """SELECT v.*, a.name as account_name, a.color as account_color
             FROM videos v JOIN accounts a ON a.id=v.account_id"""
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY v.created_at DESC LIMIT 200"
    return db.query(sql, tuple(params))


@app.post("/api/videos")
def api_video_create(body: VideoIn):
    rid = db.execute(
        """INSERT INTO videos (account_id, video_code, guion_id, title, hook, caption,
                               hashtags, niche, duration_s, file_path, thumbnail_path,
                               status, vscore_predicted, scheduled_at, hypothesis)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (body.account_id, body.video_code, body.guion_id, body.title, body.hook,
         body.caption, body.hashtags, body.niche, body.duration_s, body.file_path,
         body.thumbnail_path, body.status, body.vscore_predicted, body.scheduled_at,
         body.hypothesis),
    )
    return {"id": rid}


@app.patch("/api/videos/{vid}")
def api_video_update(vid: int, body: VideoStatusUpdate):
    fields, params = [], []
    for k in ("status", "vscore_actual", "published_at", "external_url", "outcome"):
        v = getattr(body, k, None)
        if v is not None:
            fields.append(f"{k}=?")
            params.append(v)
    if not fields:
        return {"ok": True}
    params.append(vid)
    db.execute(f"UPDATE videos SET {', '.join(fields)} WHERE id=?", tuple(params))
    return {"ok": True}


@app.delete("/api/videos/{vid}")
def api_video_delete(vid: int):
    db.execute("DELETE FROM videos WHERE id=?", (vid,))
    return {"ok": True}


# ═════════════════════════════════════════════════════════════════════════════
# API — CALENDAR (FullCalendar events feed)
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/calendar/events")
def api_calendar_events(start: Optional[str] = None, end: Optional[str] = None):
    rows = db.query(
        """SELECT v.id, v.title, v.video_code, v.status,
                  COALESCE(v.published_at, v.scheduled_at) as ts,
                  a.name as account_name, a.color as account_color
           FROM videos v JOIN accounts a ON a.id=v.account_id
           WHERE COALESCE(v.published_at, v.scheduled_at) IS NOT NULL"""
    )
    events = []
    color_by_status = {
        "published": "#10b981", "scheduled": "#fbbf24",
        "produced": "#3b82f6", "in_production": "#a855f7", "draft": "#71717a",
    }
    for r in rows:
        events.append({
            "id": r["id"],
            "title": f"{r['video_code'] or ''} {r['title']}".strip()[:60],
            "start": r["ts"],
            "color": color_by_status.get(r["status"], r["account_color"]),
            "extendedProps": {
                "account": r["account_name"], "status": r["status"],
            },
        })
    return events


# ═════════════════════════════════════════════════════════════════════════════
# API — SUGGESTIONS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/suggestions")
def api_suggestions(status: Optional[str] = None):
    if status:
        return db.query("SELECT * FROM suggestions WHERE status=? ORDER BY added_at DESC", (status,))
    return db.query("SELECT * FROM suggestions ORDER BY added_at DESC LIMIT 200")


@app.post("/api/suggestions")
def api_suggestion_create(body: SuggestionIn):
    plat = body.source_platform or _platform_from_url(body.source_url)
    rid = db.execute(
        """INSERT INTO suggestions (source_url, source_platform, title, description,
                                    view_count, duration_s, notes, added_by)
           VALUES (?,?,?,?,?,?,?,?)""",
        (body.source_url, plat, body.title, body.description, body.view_count,
         body.duration_s, body.notes, body.added_by),
    )
    return {"id": rid}


@app.patch("/api/suggestions/{sid}/status/{new_status}")
def api_suggestion_status(sid: int, new_status: str):
    db.execute("UPDATE suggestions SET status=? WHERE id=?", (new_status, sid))
    return {"ok": True}


@app.delete("/api/suggestions/{sid}")
def api_suggestion_delete(sid: int):
    db.execute("DELETE FROM suggestions WHERE id=?", (sid,))
    return {"ok": True}


def _platform_from_url(url: str) -> str:
    u = (url or "").lower()
    if "tiktok.com" in u:
        return "tiktok"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "instagram.com" in u:
        return "instagram"
    if "facebook.com" in u or "fb.watch" in u:
        return "facebook"
    return "unknown"


# ═════════════════════════════════════════════════════════════════════════════
# API — METRICS
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/api/metrics")
def api_metric_add(body: MetricsIn):
    rid = db.execute(
        """INSERT INTO metrics_snapshots (video_id, views, likes, comments, shares,
                                          saves, retention_avg, hook_rate)
           VALUES (?,?,?,?,?,?,?,?)""",
        (body.video_id, body.views, body.likes, body.comments, body.shares,
         body.saves, body.retention_avg, body.hook_rate),
    )
    return {"id": rid}


@app.get("/api/metrics/{video_id}")
def api_metrics_for_video(video_id: int):
    return db.query(
        "SELECT * FROM metrics_snapshots WHERE video_id=? ORDER BY captured_at",
        (video_id,),
    )


# ═════════════════════════════════════════════════════════════════════════════
# API — GROWTH (chart data)
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/growth/data")
def api_growth_data():
    accounts = _all_accounts()
    out = {"accounts": []}
    for a in accounts:
        rows = db.query(
            "SELECT date, followers, total_views, engagement_rate FROM account_metrics_daily WHERE account_id=? ORDER BY date",
            (a["id"],),
        )
        # If no daily snapshots, derive from video metrics
        if not rows:
            rows = db.query(
                """SELECT date(m.captured_at) as date, MAX(m.views) as total_views, NULL as followers, NULL as engagement_rate
                   FROM metrics_snapshots m JOIN videos v ON v.id=m.video_id
                   WHERE v.account_id=? GROUP BY date(m.captured_at) ORDER BY date""",
                (a["id"],),
            )
        out["accounts"].append({
            "id": a["id"], "name": a["name"], "color": a["color"], "series": rows,
        })
    return out


# ═════════════════════════════════════════════════════════════════════════════
# API — AUTOMATION
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/automation")
def api_automation():
    return db.query(
        """SELECT q.*, a.name as account_name FROM automation_queue q
           LEFT JOIN accounts a ON a.id=q.account_id ORDER BY scheduled_for"""
    )


@app.post("/api/automation")
def api_automation_create(body: AutomationIn):
    rid = db.execute(
        """INSERT INTO automation_queue (agent, action, account_id, payload, scheduled_for)
           VALUES (?,?,?,?,?)""",
        (body.agent, body.action, body.account_id,
         db.safe_json(body.payload) if body.payload else None,
         body.scheduled_for),
    )
    return {"id": rid}


@app.post("/api/automation/{qid}/run")
def api_automation_run(qid: int):
    """Manually trigger an automation queue item — marks it for execution."""
    from dashboard.services import run_automation
    return run_automation(qid)


@app.delete("/api/automation/{qid}")
def api_automation_delete(qid: int):
    db.execute("DELETE FROM automation_queue WHERE id=?", (qid,))
    return {"ok": True}


# ═════════════════════════════════════════════════════════════════════════════
# API — LEARN (calibration + patterns)
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/api/learn/calibrate")
def api_calibrate(account_id: Optional[int] = None):
    """Recompute calibration metrics from published videos."""
    from dashboard.services import calibrate_predictor
    return calibrate_predictor(account_id)


@app.post("/api/learn/scan_patterns")
def api_scan_patterns(account_id: Optional[int] = None):
    """Detect hook/niche/duration patterns in published videos."""
    from dashboard.services import scan_patterns
    return scan_patterns(account_id)


# ═════════════════════════════════════════════════════════════════════════════
# API — SEED + PIPELINE TRIGGERS
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/api/seed/run")
def api_seed_run():
    from dashboard.seed import seed_all
    return seed_all()


@app.post("/api/pipeline/produce_all")
def api_pipeline_produce():
    from dashboard.services import trigger_produce_all
    return trigger_produce_all()


@app.post("/api/pipeline/poll_metrics")
def api_pipeline_poll():
    from dashboard.services import poll_tiktok_metrics
    return poll_tiktok_metrics()


@app.get("/api/learn/status")
def api_learn_status():
    """Estado actual del ciclo autónomo de aprendizaje."""
    # Leer último reporte de calibración si existe
    calib = db.query_one(
        "SELECT mae, bias, is_calibrated, computed_at FROM calibration_log "
        "ORDER BY computed_at DESC LIMIT 1"
    )
    patterns_count = db.query_one("SELECT COUNT(*) n FROM learn_patterns")
    svr_count = db.query_one("SELECT COUNT(*) n FROM simulations_vs_reality")
    weight_ver = db.query_one(
        "SELECT version, mae_before, mae_after, committed_at "
        "FROM vscore_weight_history ORDER BY version DESC LIMIT 1"
    )
    return {
        "scheduler": {
            "running": _learn_state["running"],
            "last_run_at": _learn_state["last_run_at"],
            "next_run_at": _learn_state["next_run_at"],
            "total_runs": _learn_state["runs"],
        },
        "calibration": calib,
        "patterns_count": patterns_count["n"] if patterns_count else 0,
        "sim_vs_reality_count": svr_count["n"] if svr_count else 0,
        "weight_version": weight_ver,
        "last_result_status": (
            (_learn_state["last_result"] or {}).get("status", "never_run")
        ),
    }


@app.post("/api/learn/cycle")
def api_learn_cycle():
    """Dispara el ciclo M6 LEARN en background (no bloquea). Idempotente."""
    if _learn_state["running"]:
        return {"ok": False, "status": "already_running",
                "running_since": _learn_state["last_run_at"]}
    _schedule_learn_cycle()
    return {"ok": True, "status": "started",
            "message": "Ciclo M6 LEARN arrancado. Ver /api/learn/status para progreso."}


@app.post("/api/learn/schedule_recurring")
def api_learn_schedule_recurring(hours: int = 6, repeats: int = 4):
    """Inserta `repeats` tareas en automation_queue espaciadas cada `hours` horas."""
    import datetime as _dt
    now = _dt.datetime.utcnow()
    ids = []
    for i in range(1, repeats + 1):
        sched = (now + _dt.timedelta(hours=i * hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rid = db.execute(
            """INSERT INTO automation_queue
                 (agent, action, account_id, payload, scheduled_for, status)
               VALUES (?,?,?,?,?,?)""",
            ("A7", "learn_cycle", 1,
             db.safe_json({"interval_hours": hours, "index": i}),
             sched, "pending")
        )
        ids.append(rid)
    return {"scheduled": ids}


# ═════════════════════════════════════════════════════════════════════════════
# API — OFICINA (Pokemon-style live agents view)
# ═════════════════════════════════════════════════════════════════════════════

_AGENT_ROLES = {
    "A0": "Director Orquestador",
    "A1": "Investigacion Mercado",
    "A2": "Psicologia Marketing",
    "A3": "Estratega Algoritmico",
    "A4": "Editor de Video",
    "A5": "Logistica Campanas",
    "A6": "Operaciones Publicacion",
    "A7": "Supervision Evolutiva",
    "A8": "Analisis y Prediccion",
    "A9": "Compliance Legal",
}


@app.get("/api/oficina/state")
def api_oficina_state():
    """Live state for the Pokemon-style office view.
    Derives per-agent activity from automation_queue + recent videos / simulations / suggestions.
    """
    import time

    # ── token bar (read .claude/token_state.json if present) ────────────────
    tokens_pct = 85.0
    token_file = ROOT / ".claude" / "token_state.json"
    if token_file.exists():
        try:
            data = json.loads(token_file.read_text(encoding="utf-8"))
            tokens_pct = float(data.get("pct", 85))
        except Exception:
            pass

    # ── sprint ───────────────────────────────────────────────────────────────
    last_brief = db.query_one(
        "SELECT sprint_number FROM briefings ORDER BY date DESC LIMIT 1"
    )
    sprint = last_brief["sprint_number"] if last_brief else 3

    # ── agent skeleton ──────────────────────────────────────────────────────
    agents: dict[str, dict] = {
        aid: {
            "id": aid,
            "role": role,
            "status": "idle",
            "current_task": None,
            "recent_log": [],
        }
        for aid, role in _AGENT_ROLES.items()
    }

    # ── automation_queue → working / pending ────────────────────────────────
    queue = db.query(
        """SELECT agent, action, status, started_at, completed_at
           FROM automation_queue
           WHERE agent IS NOT NULL
           ORDER BY
             CASE status WHEN 'in_progress' THEN 0 WHEN 'pending' THEN 1 ELSE 2 END,
             COALESCE(started_at, created_at) DESC
           LIMIT 80"""
    )
    for q in queue:
        aid = (q["agent"] or "").upper()
        if aid not in agents:
            continue
        st = (q["status"] or "").lower()
        if st == "in_progress" and not agents[aid]["current_task"]:
            agents[aid]["status"] = "working"
            agents[aid]["current_task"] = q["action"] or "ejecutando tarea"
        elif st in ("done", "completed") and len(agents[aid]["recent_log"]) < 4:
            agents[aid]["recent_log"].append(f"{q['action']} — completado")

    # ── recent videos → A4 editor ───────────────────────────────────────────
    recent_videos = db.query(
        """SELECT title, status, created_at FROM videos
           WHERE datetime(created_at) >= datetime('now', '-2 hours')
           ORDER BY created_at DESC LIMIT 4"""
    )
    for v in recent_videos:
        agents["A4"]["recent_log"].append(f"edicion: {(v['title'] or '')[:38]}")
    if recent_videos and agents["A4"]["status"] == "idle":
        agents["A4"]["status"] = "working"
        agents["A4"]["current_task"] = f"editando: {recent_videos[0]['title'][:32]}"

    # ── recently published → A6 ops ─────────────────────────────────────────
    pub = db.query(
        """SELECT title, published_at FROM videos
           WHERE status='published' AND datetime(published_at) >= datetime('now', '-24 hours')
           ORDER BY published_at DESC LIMIT 4"""
    )
    for v in pub:
        agents["A6"]["recent_log"].append(f"publicado: {(v['title'] or '')[:38]}")

    # ── recent simulations → A8 analytics ───────────────────────────────────
    sims = db.query(
        """SELECT v.title, s.vscore_computed FROM simulations s
           JOIN videos v ON v.id = s.video_id
           WHERE datetime(s.captured_at) >= datetime('now', '-2 hours')
           ORDER BY s.captured_at DESC LIMIT 4"""
    )
    for s in sims:
        score = s.get("vscore_computed") or 0
        agents["A8"]["recent_log"].append(
            f"V-Score {score:.0f}: {(s['title'] or '')[:30]}"
        )
    if sims and agents["A8"]["status"] == "idle":
        agents["A8"]["status"] = "working"
        agents["A8"]["current_task"] = "calculando V-Score predictivo"

    # ── recent suggestions → A1 research ────────────────────────────────────
    sugg = db.query(
        """SELECT title FROM suggestions
           WHERE datetime(added_at) >= datetime('now', '-6 hours')
           ORDER BY added_at DESC LIMIT 4"""
    )
    for s in sugg:
        agents["A1"]["recent_log"].append(f"outlier: {(s['title'] or '')[:38]}")
    if sugg and agents["A1"]["status"] == "idle":
        agents["A1"]["status"] = "working"
        agents["A1"]["current_task"] = "outlier hunting multi-plataforma"

    # ── patterns → A7 supervision ──────────────────────────────────────────
    patterns = db.query(
        "SELECT pattern_type, pattern_value FROM learn_patterns ORDER BY detected_at DESC LIMIT 3"
    )
    for p in patterns:
        agents["A7"]["recent_log"].append(
            f"patron {p['pattern_type']}: {(p['pattern_value'] or '')[:28]}"
        )

    # ── calibrations → A8 cross ─────────────────────────────────────────────
    calib = db.query_one(
        "SELECT mae, sample_size FROM calibration_log ORDER BY computed_at DESC LIMIT 1"
    )
    if calib:
        agents["A8"]["recent_log"].insert(
            0, f"calibracion n={calib['sample_size']} MAE={calib['mae']:.2f}"
        )

    # ── briefings → A0 director ─────────────────────────────────────────────
    last_brief_full = db.query_one(
        "SELECT sprint_number, date, status_summary FROM briefings ORDER BY date DESC LIMIT 1"
    )
    if last_brief_full:
        agents["A0"]["recent_log"].append(
            f"briefing sprint {last_brief_full['sprint_number']} publicado"
        )
        agents["A0"]["current_task"] = "supervisando sprint en curso"
        agents["A0"]["status"] = "working"

    # ── compliance always vigilant ──────────────────────────────────────────
    if agents["A9"]["status"] == "idle":
        agents["A9"]["status"] = "working"
        agents["A9"]["current_task"] = "auditando licencias y ToS"
        agents["A9"]["recent_log"].append("0 strikes · 0 DMCA · sistema OK")

    # ── psicologia / algoritmo / logistica baseline tasks ──────────────────
    if agents["A2"]["status"] == "idle":
        agents["A2"]["current_task"] = "disenando hooks 0-3s"
        agents["A2"]["status"] = "working"
    if agents["A3"]["status"] == "idle":
        agents["A3"]["current_task"] = "analizando trending sounds"
        agents["A3"]["status"] = "working"
    if agents["A5"]["status"] == "idle":
        agents["A5"]["current_task"] = "en pausa (presupuesto $0)"
        agents["A5"]["status"] = "idle"

    # ── meeting simulation (rotates every ~90s; idle 20% of the time) ──────
    now_s = int(time.time())
    meeting_topics = [
        ("Revision V-Score sprint", ["A0", "A2", "A4", "A8"]),
        ("Compliance check pre-publicacion", ["A0", "A6", "A9"]),
        ("Briefing semanal de planificacion", ["A0", "A1", "A2", "A3", "A6"]),
        ("Retrospectiva del sprint anterior", ["A0", "A7", "A1", "A4"]),
        ("Audiencia: arco emocional V-nuevo", ["A2", "A4", "A8"]),
    ]
    bucket = (now_s // 90) % len(meeting_topics)
    meeting_off = (now_s // 45) % 5 == 0  # ~20% idle
    if meeting_off:
        meeting = {"active": False, "participants": [], "topic": ""}
    else:
        topic, parts = meeting_topics[bucket]
        meeting = {"active": True, "participants": parts, "topic": topic}
        for aid in parts:
            if aid in agents:
                agents[aid]["status"] = "meeting"

    # ── recent events (cross-agent ticker) ──────────────────────────────────
    events: list[dict] = []
    for v in pub[:2]:
        events.append({"agent": "A6", "message": f"publico '{(v['title'] or '')[:32]}'"})
    for s in sims[:2]:
        score = s.get("vscore_computed") or 0
        events.append({"agent": "A8", "message": f"V-Score {score:.0f} en '{(s['title'] or '')[:24]}'"})
    for s in sugg[:2]:
        events.append({"agent": "A1", "message": f"outlier nuevo: '{(s['title'] or '')[:28]}'"})
    if not events:
        events.append({"agent": "A0", "message": "todo bajo control. agentes en sus puestos."})

    return {
        "tokens_pct": round(tokens_pct, 1),
        "sprint": sprint,
        "agents": list(agents.values()),
        "meeting": meeting,
        "recent_events": events[:6],
        "ts": now_s,
    }


# ═════════════════════════════════════════════════════════════════════════════
# API — FEEDBACK (user → Claude Code communication channel)
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/feedback")
def api_feedback(status: Optional[str] = None):
    if status:
        return db.query(
            "SELECT * FROM user_feedback WHERE status=? ORDER BY created_at DESC", (status,)
        )
    return db.query("SELECT * FROM user_feedback ORDER BY created_at DESC LIMIT 200")


@app.post("/api/feedback")
def api_feedback_create(body: FeedbackIn):
    rid = db.execute(
        """INSERT INTO user_feedback (type, priority, message, context)
           VALUES (?,?,?,?)""",
        (body.type, body.priority, body.message, body.context),
    )
    _sync_feedback_to_vault(rid, body)
    return {"id": rid, "status": "pendiente"}


@app.patch("/api/feedback/{fid}/status/{new_status}")
def api_feedback_status(fid: int, new_status: str):
    db.execute("UPDATE user_feedback SET status=? WHERE id=?", (new_status, fid))
    return {"ok": True}


@app.patch("/api/feedback/{fid}/respond")
def api_feedback_respond(fid: int, response: str = Form(...)):
    db.execute(
        "UPDATE user_feedback SET response=?, status='resuelto', responded_at=datetime('now') WHERE id=?",
        (response, fid),
    )
    return {"ok": True}


@app.delete("/api/feedback/{fid}")
def api_feedback_delete(fid: int):
    db.execute("DELETE FROM user_feedback WHERE id=?", (fid,))
    return {"ok": True}


def _sync_feedback_to_vault(fid: int, body: FeedbackIn):
    """Write feedback to obsidian vault so agents can read it during sprints."""
    inbox = ROOT / "obsidian_vault" / "00_Inbox" / "feedback"
    inbox.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M")
    path = inbox / f"{ts}_fb{fid}_{body.type}.md"
    path.write_text(
        f"---\nid: {fid}\ntype: {body.type}\npriority: {body.priority}\n"
        f"status: pendiente\nfecha: {ts}\n---\n\n"
        f"## {body.type.upper()}\n\n{body.message}\n\n"
        + (f"**Contexto:** {body.context}\n" if body.context else ""),
        encoding="utf-8",
    )


# ═════════════════════════════════════════════════════════════════════════════
# Health
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "db": str(db.DB_PATH)}
