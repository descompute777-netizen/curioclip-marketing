"""
CurioClip Mission Control — FastAPI application.

Sections (each a router):
  - / (home) → overview HTML
  - /partial/<section> → HTMX-loaded panels
  - /api/accounts, /api/videos, /api/suggestions, ...
"""
import json
import os
import sys
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
    AccountIn, VideoIn, SuggestionIn, MetricsIn, AutomationIn, VideoStatusUpdate
)

# ─── App init ───────────────────────────────────────────────────────────────

app = FastAPI(title="CurioClip Mission Control", version="1.0.0")

templates = Jinja2Templates(directory=str(HERE / "templates"))
templates.env.filters["money"] = lambda v: f"{v:,}".replace(",", ".")
templates.env.filters["pct"] = lambda v: f"{(v or 0)*100:.1f}%"
templates.env.filters["short"] = lambda v, n=80: (v[:n] + "...") if v and len(v) > n else (v or "")

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
               ORDER BY confidence DESC LIMIT 30"""
        )

    elif section == "briefings":
        ctx["briefings"] = db.query(
            "SELECT * FROM briefings ORDER BY date DESC LIMIT 12"
        )

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


# ═════════════════════════════════════════════════════════════════════════════
# Health
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "db": str(db.DB_PATH)}
