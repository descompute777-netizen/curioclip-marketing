"""
Seeder: auto-poblate the DB from existing artifacts in the project:
  - configs/v*.py (captions, hooks, hashtags)
  - obsidian_vault/40_Publicacion/schedule_sprint*.json (schedule)
  - obsidian_vault/SEMANAS/*/*/OUTPUT/V*_final.mp4 (file paths)
  - obsidian_vault/30_Contenido/cola/*.md (script queue → suggestions)

Idempotent: safe to run repeatedly. Uses UPSERT-like guards.
"""
import re
import json
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta

from dashboard import db

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "obsidian_vault"
SEMANAS = VAULT / "SEMANAS"
CONFIGS = ROOT / "configs"
COLA = VAULT / "30_Contenido" / "cola"


def _load_config_module(path: Path) -> dict | None:
    """Load a configs/v*.py module dynamically and return VIDEO_CONFIG."""
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, "VIDEO_CONFIG", None)
    except Exception as e:
        print(f"[SEED] Failed to load {path.name}: {e}")
        return None


def ensure_default_account() -> int:
    """Make sure the main CurioClip TikTok account exists. Returns its id."""
    row = db.query_one(
        "SELECT id FROM accounts WHERE handle='curioclip' AND platform='tiktok'"
    )
    if row:
        return row["id"]
    return db.execute(
        """INSERT INTO accounts (name, handle, platform, niche, color,
                                 followers_current, followers_goal, notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        ("CurioClip", "curioclip", "tiktok", "Curiosidades / Datos curiosos",
         "#fbbf24", 0, 10000, "Cuenta principal — seed automatica del dashboard"),
    )


def seed_videos_from_configs(account_id: int) -> int:
    """Read configs/v*.py and upsert into videos table."""
    count = 0
    for cfg_path in sorted(CONFIGS.glob("v*.py")):
        if cfg_path.name == "__init__.py":
            continue
        cfg = _load_config_module(cfg_path)
        if not cfg:
            continue
        vc = cfg.get("video_id")
        title = (cfg.get("caption_tiktok") or "")[:120].strip().rstrip(".") or vc
        caption = cfg.get("caption_tiktok") or ""
        # Extract hashtags
        hashtags = " ".join(re.findall(r"#\w+", caption))

        # Find output file
        file_path = ""
        for sem_dir in SEMANAS.glob("SEMANA_*"):
            for day_dir in sem_dir.iterdir():
                out = day_dir / "OUTPUT" / f"{vc}_final.mp4"
                if out.exists():
                    file_path = str(out)
                    break
            if file_path:
                break

        # Status inference: file exists → at least produced
        status = "produced" if file_path else "draft"
        # If we have a published_at via captions presence, mark published — but we
        # don't know without metrics. Leave at "produced" by default.

        # Hook = first sentence of caption
        hook = caption.split(".")[0][:160] if caption else None
        duration = None

        existing = db.query_one(
            "SELECT id FROM videos WHERE video_code=? AND account_id=?",
            (vc, account_id),
        )
        if existing:
            db.execute(
                """UPDATE videos SET title=?, hook=?, caption=?, hashtags=?,
                                     file_path=?, status=COALESCE(status, ?)
                   WHERE id=?""",
                (title, hook, caption, hashtags, file_path, status, existing["id"]),
            )
        else:
            db.execute(
                """INSERT INTO videos (account_id, video_code, title, hook, caption,
                                       hashtags, file_path, status, niche)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (account_id, vc, title, hook, caption, hashtags, file_path,
                 status, "curiosidades"),
            )
            count += 1
    return count


def seed_published_videos_v1_v7(account_id: int) -> int:
    """Mark V1-V7 as published with their known publish times from this sprint."""
    published = {
        "V1": ("2026-05-15T05:55:00Z", "El animal que NO puede morir"),
        "V2": ("2026-05-15T01:00:00Z", "Tu cuerpo tiene MAS bacterias que estrellas"),
        "V3": ("2026-05-16T14:00:00Z", "Desde 1973 esta radio rusa transmite"),
        "V4": ("2026-05-17T03:00:00Z", "Leyes absurdas de Estados Unidos"),
        "V5": ("2026-05-18T19:22:00Z", "Algo destruyo 2,000 km2 de bosque"),
        "V6": ("2026-05-18T19:25:00Z", "Conan: bacteria sobrevive bomba nuclear"),
        "V7": ("2026-05-18T19:40:00Z", "Hazte cosquillas a ti mismo"),
    }
    count = 0
    for code, (pub_at, _title) in published.items():
        existing = db.query_one(
            "SELECT id FROM videos WHERE video_code=? AND account_id=?",
            (code, account_id),
        )
        if not existing:
            continue
        db.execute(
            """UPDATE videos SET status='published', published_at=?,
                                 vscore_predicted=COALESCE(vscore_predicted, ?)
               WHERE id=?""",
            (pub_at, _score_for(code), existing["id"]),
        )
        count += 1
    return count


def _score_for(code: str) -> float:
    mapping = {"V1": 8.0, "V2": 9.0, "V3": 7.6, "V4": 7.5, "V5": 8.9, "V6": 8.2, "V7": 8.1}
    return mapping.get(code, 7.0)


def seed_initial_metrics(account_id: int) -> int:
    """Seed initial metrics snapshots from the data we know. Idempotent — skips
    videos that already have any snapshot."""
    known = {"V5": 37, "V6": 30, "V7": 0}
    count = 0
    for code, views in known.items():
        v = db.query_one(
            "SELECT id FROM videos WHERE video_code=? AND account_id=?",
            (code, account_id),
        )
        if not v:
            continue
        existing = db.query_one(
            "SELECT id FROM metrics_snapshots WHERE video_id=?", (v["id"],),
        )
        if existing:
            continue
        db.execute(
            """INSERT INTO metrics_snapshots (video_id, views, likes, comments, shares)
               VALUES (?,?,?,?,?)""",
            (v["id"], views, 0, 0, 0),
        )
        count += 1
    return count


def seed_suggestions_from_cola(account_id: int) -> int:
    """Read the script queue and create suggestions for top-V-Score scripts."""
    queue_file = COLA / "sprint2_guiones_outlier.md"
    if not queue_file.exists():
        return 0
    text = queue_file.read_text(encoding="utf-8")
    blocks = re.split(r"\n### G(\d+) — ", text)[1:]
    count = 0
    for i in range(0, len(blocks), 2):
        gid = blocks[i]
        body = blocks[i + 1]
        title_line = body.splitlines()[0]
        hook_match = re.search(r"\*\*HOOK \(0-3s\):\*\*\s*\"([^\"]+)\"", body)
        score_match = re.search(r"V[-_]?(\d+(?:\.\d+)?)", body)
        if not hook_match:
            continue
        # skip if it's already a produced video (G04, G09, G15 = V5,V6,V7)
        if gid in ("04", "09", "15"):
            continue
        existing = db.query_one(
            "SELECT id FROM suggestions WHERE source_url=?",
            (f"internal:G{gid}",),
        )
        if existing:
            continue
        db.execute(
            """INSERT INTO suggestions (source_url, source_platform, title, description,
                                        score, hook_extracted, status, added_by)
               VALUES (?,?,?,?,?,?,?,?)""",
            (f"internal:G{gid}", "internal",
             f"G{gid} — {title_line.strip()}", body[:500],
             float(score_match.group(1)) if score_match else None,
             hook_match.group(1), "inbox", "outlier-cloning-sprint2"),
        )
        count += 1
    return count


def seed_automation_queue(account_id: int) -> int:
    """Seed default recurring agent tasks for the next 24-72h."""
    now = datetime.utcnow()
    items = [
        ("A1", "scan_outliers", now + timedelta(hours=2)),
        ("A6", "poll_metrics", now + timedelta(hours=1)),
        ("A8", "calibrate", now + timedelta(hours=24)),
        ("A1", "scan_patterns", now + timedelta(hours=12)),
        ("A0", "weekly_briefing", now + timedelta(days=7)),
    ]
    count = 0
    for agent, action, when in items:
        existing = db.query_one(
            "SELECT id FROM automation_queue WHERE agent=? AND action=? AND status='pending'",
            (agent, action),
        )
        if existing:
            continue
        db.execute(
            """INSERT INTO automation_queue (agent, action, account_id, scheduled_for)
               VALUES (?,?,?,?)""",
            (agent, action, account_id, when.strftime("%Y-%m-%dT%H:%M:%SZ")),
        )
        count += 1
    return count


def seed_briefing_initial(account_id: int) -> int:
    """Insert the Sprint 2/3 briefing we just authored."""
    existing = db.query_one("SELECT id FROM briefings WHERE sprint_number=3")
    if existing:
        return 0
    kpis = {
        "videos_publicados_hoy": 3,
        "publicaciones_acumuladas": 23,
        "v5_vistas_iniciales": 37,
        "v6_vistas_iniciales": 30,
    }
    db.execute(
        """INSERT INTO briefings (sprint_number, date, status_summary, kpis_json,
                                  decisions, next_steps, blockers)
           VALUES (?,?,?,?,?,?,?)""",
        (3, "2026-05-18",
         "3 videos producidos y publicados autonomamente en TikTok (V5/V6/V7). Pipeline end-to-end ejecutado en ~25 min. Sin intervencion manual.",
         db.safe_json(kpis),
         "Cambie G01 Napoleon por G09 Conan bacterium por instruccion del usuario. V5 recodificado a CRF 28 para entrar bajo limite Playwright 50MB.",
         "M6 LEARN en 24h/72h. Sprint 3 continuacion: G07 WOW Signal, G03 Capital 1 dia, G24 Sol desaparece.",
         "Composio TikTok OAuth sigue pendiente (7-14 dias). Mientras tanto Playwright funciona pero requiere Chrome bridge corriendo."),
    )
    return 1


def seed_all() -> dict:
    """Run the entire seed pipeline. Idempotent."""
    db.init_db()
    aid = ensure_default_account()
    vids = seed_videos_from_configs(aid)
    pubs = seed_published_videos_v1_v7(aid)
    metrics = seed_initial_metrics(aid)
    suggs = seed_suggestions_from_cola(aid)
    automs = seed_automation_queue(aid)
    briefs = seed_briefing_initial(aid)
    return {
        "account_id": aid,
        "videos_inserted": vids,
        "videos_marked_published": pubs,
        "metrics_snapshots": metrics,
        "suggestions_imported": suggs,
        "automation_tasks_scheduled": automs,
        "briefings_added": briefs,
    }


if __name__ == "__main__":
    print(json.dumps(seed_all(), indent=2, ensure_ascii=False))
