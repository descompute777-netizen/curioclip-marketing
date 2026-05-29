"""
evolution_engine.py — El cerebro autonomo del sistema de analitica.

Lee datos reales → detecta patrones → detecta restricciones → rastrea crecimiento
→ evoluciona la estrategia → escribe config/content_strategy.json → los generadores
de contenido lo leen y se adaptan automaticamente.

Ciclo: MEASURE → ANALYZE → EVOLVE → (content generators read strategy) → PUBLISH → repeat

Corre como parte del learn_cycle.py o standalone cada 6h.
"""
from __future__ import annotations
import sys, json, sqlite3, datetime, math
from pathlib import Path
from collections import defaultdict
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "dashboard" / "curioclip.db"
STRATEGY = ROOT / "config" / "content_strategy.json"
ALERTS_DIR = ROOT / "obsidian_vault" / "40_Publicacion" / "alerts"
VAULT = ROOT / "obsidian_vault"

START_DATE = datetime.date(2026, 5, 6)
GOAL_FOLLOWERS = 10000
GOAL_VIEWS = 100000
GOAL_DAYS = 90

NOW = datetime.datetime.utcnow()
TODAY = NOW.date()
DAYS_ELAPSED = (TODAY - START_DATE).days
DAYS_REMAINING = max(GOAL_DAYS - DAYS_ELAPSED, 1)


def load_strategy() -> dict:
    if STRATEGY.exists():
        return json.loads(STRATEGY.read_text(encoding="utf-8"))
    return {}


def save_strategy(strat: dict):
    strat["updated_at"] = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
    strat["updated_by"] = "evolution_engine"
    STRATEGY.parent.mkdir(parents=True, exist_ok=True)
    STRATEGY.write_text(json.dumps(strat, ensure_ascii=False, indent=2), encoding="utf-8")


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    return con


# ═══════════════════════════════════════════════════════════════════════════════
# 1. GROWTH VELOCITY TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

def track_growth(con: sqlite3.Connection, strat: dict) -> dict:
    """Track followers and views velocity against 90-day goals."""
    # Current totals from accounts table
    row = con.execute(
        "SELECT COALESCE(SUM(followers_current),0) f, COALESCE(SUM(views_total),0) v "
        "FROM accounts WHERE status='active'"
    ).fetchone()
    followers_now = row["f"] or 0
    views_now = row["v"] or 0

    # Also sum video views from metrics
    mv = con.execute(
        "SELECT COALESCE(SUM(sub.max_views),0) total FROM "
        "(SELECT MAX(views) max_views FROM metrics_snapshots GROUP BY video_id) sub"
    ).fetchone()
    views_from_metrics = mv["total"] or 0
    views_now = max(views_now, views_from_metrics)

    # Daily snapshots for velocity calculation
    daily = con.execute(
        "SELECT date, followers, total_views FROM account_metrics_daily "
        "WHERE account_id=1 ORDER BY date DESC LIMIT 14"
    ).fetchall()

    followers_per_day = 0.0
    views_per_day = 0.0
    if len(daily) >= 2:
        newest, oldest = daily[0], daily[-1]
        span_days = max(1, (datetime.date.fromisoformat(newest["date"]) -
                            datetime.date.fromisoformat(oldest["date"])).days)
        if newest["followers"] and oldest["followers"]:
            followers_per_day = (newest["followers"] - oldest["followers"]) / span_days
        if newest["total_views"] and oldest["total_views"]:
            views_per_day = (newest["total_views"] - oldest["total_views"]) / span_days

    followers_needed = (GOAL_FOLLOWERS - followers_now) / DAYS_REMAINING
    views_needed = (GOAL_VIEWS - views_now) / DAYS_REMAINING

    on_track = followers_per_day >= followers_needed * 0.7
    if followers_per_day < followers_needed * 0.3:
        trajectory = "critical"
    elif followers_per_day < followers_needed * 0.7:
        trajectory = "behind"
    elif followers_per_day < followers_needed * 1.3:
        trajectory = "on_track"
    else:
        trajectory = "ahead"

    growth = {
        "followers_current": followers_now,
        "followers_goal": GOAL_FOLLOWERS,
        "views_accumulated": views_now,
        "views_goal": GOAL_VIEWS,
        "followers_per_day_avg": round(followers_per_day, 2),
        "views_per_day_avg": round(views_per_day, 1),
        "days_elapsed": DAYS_ELAPSED,
        "days_remaining": DAYS_REMAINING,
        "followers_needed_per_day": round(followers_needed, 1),
        "views_needed_per_day": round(views_needed, 1),
        "on_track": on_track,
        "trajectory": trajectory,
    }
    strat["growth"] = growth

    if trajectory == "critical":
        _alert("GROWTH_CRITICAL",
               f"Crecimiento critico: {followers_per_day:.1f} seg/dia vs {followers_needed:.1f} necesarios. "
               f"Faltan {DAYS_REMAINING} dias para la meta.", "urgente")
    elif trajectory == "behind":
        _alert("GROWTH_BEHIND",
               f"Crecimiento por debajo del ritmo: {followers_per_day:.1f} seg/dia vs "
               f"{followers_needed:.1f} necesarios.", "alta")

    print(f"[GROWTH] {trajectory.upper()} | {followers_now}/{GOAL_FOLLOWERS} followers "
          f"| {followers_per_day:.1f}/dia (need {followers_needed:.1f}/dia) "
          f"| {DAYS_REMAINING}d remaining")
    return growth


# ═══════════════════════════════════════════════════════════════════════════════
# 2. RESTRICTION / SHADOWBAN DETECTOR
# ═══════════════════════════════════════════════════════════════════════════════

def detect_restrictions(con: sqlite3.Connection, strat: dict):
    """Detect videos that may be restricted or shadowbanned by TikTok."""
    rows = con.execute("""
        SELECT v.id, v.video_code, v.title, v.published_at,
               m.views, m.likes, m.comments, m.captured_at
        FROM videos v
        JOIN metrics_snapshots m ON m.video_id = v.id
        WHERE v.status = 'published'
        ORDER BY v.id, m.captured_at
    """).fetchall()

    # Group metrics by video
    by_video: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_video[r["video_code"] or f"id_{r['id']}"].append(dict(r))

    restricted = []
    all_vph = []

    for code, snapshots in by_video.items():
        if len(snapshots) < 1:
            continue
        latest = snapshots[-1]
        pub = latest.get("published_at")
        if not pub:
            continue
        try:
            pub_dt = datetime.datetime.strptime(
                pub.replace("Z", "").replace("T", " ").split(".")[0],
                "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue

        hours = max((NOW - pub_dt).total_seconds() / 3600, 0.5)
        views = latest["views"] or 0
        vph = views / hours
        all_vph.append(vph)

        # Restriction signals:
        # 1. Video older than 48h with <100 views (very low for any account)
        # 2. Views/hour significantly below account average
        # 3. Zero engagement despite views
        if hours > 48 and views < 100:
            restricted.append({
                "video_code": code,
                "views": views,
                "hours_live": round(hours, 1),
                "vph": round(vph, 2),
                "signal": "extremely_low_views",
            })
        elif hours > 24 and views > 0:
            er = ((latest["likes"] or 0) + (latest["comments"] or 0)) / views
            if er < 0.005 and views < 500:
                restricted.append({
                    "video_code": code,
                    "views": views,
                    "er": round(er, 4),
                    "signal": "zero_engagement",
                })

    # Check for account-level shadowban: if recent videos all have much lower VPH
    if len(all_vph) >= 5:
        avg_vph = mean(all_vph)
        recent_3 = all_vph[-3:]
        recent_avg = mean(recent_3)
        if avg_vph > 0 and recent_avg < avg_vph * 0.3:
            _alert("SHADOWBAN_POSSIBLE",
                   f"Los 3 videos mas recientes promedian {recent_avg:.1f} vph vs "
                   f"promedio historico {avg_vph:.1f} vph (caida de {(1 - recent_avg/avg_vph)*100:.0f}%). "
                   f"Posible shadowban.", "urgente")
            strat.setdefault("restrictions", {})["shadowban_risk"] = "high"
        else:
            strat.setdefault("restrictions", {})["shadowban_risk"] = "none"

    strat.setdefault("restrictions", {})["detected"] = len(restricted) > 0
    strat["restrictions"]["restricted_videos"] = restricted
    strat["restrictions"]["last_check"] = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")

    if restricted:
        codes = ", ".join(r["video_code"] for r in restricted)
        _alert("VIDEOS_RESTRICTED",
               f"{len(restricted)} videos con señales de restriccion: {codes}. "
               f"Revisar contenido y hashtags.", "alta")

    print(f"[RESTRICT] {len(restricted)} restricted | shadowban_risk: "
          f"{strat['restrictions'].get('shadowban_risk', 'unknown')}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. NICHE WEIGHT EVOLUTION
# ═══════════════════════════════════════════════════════════════════════════════

def evolve_niche_weights(con: sqlite3.Connection, strat: dict):
    """Adjust niche weights based on real performance data."""
    patterns = con.execute(
        "SELECT pattern_value, avg_views, avg_engagement, sample_size, confidence "
        "FROM learn_patterns WHERE pattern_type='niche' AND confidence >= 0.2 "
        "ORDER BY avg_views DESC"
    ).fetchall()

    if not patterns:
        print("[NICHE] No pattern data — keeping defaults")
        return

    # Compute weights proportional to performance (views_per_hour * engagement)
    scored = []
    for p in patterns:
        score = (p["avg_views"] or 1) * (1 + (p["avg_engagement"] or 0))
        scored.append((p["pattern_value"], score, p["sample_size"]))

    total_score = sum(s for _, s, _ in scored)
    if total_score == 0:
        return

    new_weights = {}
    for niche, score, n in scored:
        raw_weight = score / total_score
        # Blend with exploration: 70% data-driven + 30% uniform (ensure variety)
        uniform = 1.0 / max(len(scored), 1)
        blended = 0.7 * raw_weight + 0.3 * uniform
        new_weights[niche] = round(blended, 3)

    # Ensure weights sum to ~1.0
    total = sum(new_weights.values())
    if total > 0:
        new_weights = {k: round(v / total, 3) for k, v in new_weights.items()}

    old_weights = strat.get("niche_weights", {})
    if old_weights != new_weights:
        strat["niche_weights"] = new_weights
        changes = []
        for k in set(list(old_weights.keys()) + list(new_weights.keys())):
            old_v = old_weights.get(k, 0)
            new_v = new_weights.get(k, 0)
            if abs(old_v - new_v) > 0.02:
                direction = "UP" if new_v > old_v else "DOWN"
                changes.append(f"{k}: {old_v:.0%}→{new_v:.0%} ({direction})")
        if changes:
            print(f"[NICHE] Weights evolved: {', '.join(changes)}")
        else:
            print(f"[NICHE] Minor adjustments, {len(new_weights)} niches")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. VOICE / HOOK / DURATION / HOUR EVOLUTION
# ═══════════════════════════════════════════════════════════════════════════════

def evolve_production_params(con: sqlite3.Connection, strat: dict):
    """Evolve voice, hook, duration, and posting hour preferences."""
    # Voice preferences
    voices = con.execute(
        "SELECT pattern_value, avg_views, sample_size FROM learn_patterns "
        "WHERE pattern_type='voice' AND confidence >= 0.2 ORDER BY avg_views DESC"
    ).fetchall()
    if voices:
        top_voices = [v["pattern_value"] for v in voices[:3] if v["pattern_value"] != "unknown"]
        bottom_voices = [v["pattern_value"] for v in voices[-2:] if v["pattern_value"] != "unknown"]
        strat.setdefault("voice_preferences", {})["top_voices"] = top_voices
        strat["voice_preferences"]["avoid_voices"] = bottom_voices
        print(f"[VOICE] Top: {top_voices[:3]} | Avoid: {bottom_voices}")

    # Duration sweet spot
    durations = con.execute(
        "SELECT pattern_value, avg_views FROM learn_patterns "
        "WHERE pattern_type='duration_bucket' AND confidence >= 0.2 ORDER BY avg_views DESC LIMIT 1"
    ).fetchone()
    if durations:
        bucket = durations["pattern_value"]
        mapping = {
            "short_<40s": [28, 38], "mid_40_60s": [40, 58],
            "long_60_80s": [60, 78], "xlong_>80s": [80, 95],
        }
        if bucket in mapping:
            strat["target_duration_range_s"] = mapping[bucket]
            print(f"[DURATION] Target: {mapping[bucket]}s (from {bucket})")

    # Optimal hours
    hours = con.execute(
        "SELECT pattern_value, avg_views FROM learn_patterns "
        "WHERE pattern_type='hour_bucket' AND confidence >= 0.2 ORDER BY avg_views DESC"
    ).fetchall()
    if hours:
        hour_map = {
            "early_0_6": [3], "morning_6_12": [9, 11],
            "afternoon_12_18": [15, 17], "evening_18_24": [19, 21, 23],
        }
        optimal = []
        for h in hours[:2]:
            optimal.extend(hour_map.get(h["pattern_value"], []))
        if optimal:
            strat["optimal_posting_hours_utc"] = sorted(set(optimal))[:4]
            print(f"[HOURS] Optimal UTC: {strat['optimal_posting_hours_utc']}")

    # Hook patterns
    hooks = con.execute(
        "SELECT pattern_value, avg_views, sample_size FROM learn_patterns "
        "WHERE pattern_type='hook_first' AND confidence >= 0.2 ORDER BY avg_views DESC"
    ).fetchall()
    if hooks:
        top_hooks = [h["pattern_value"] for h in hooks[:5] if h["pattern_value"] != "?"]
        worst_hooks = [h["pattern_value"] for h in hooks[-3:] if h["pattern_value"] != "?"]
        strat.setdefault("hook_patterns", {})["preferred_starts"] = top_hooks
        strat["hook_patterns"]["avoid_patterns"] = worst_hooks
        print(f"[HOOKS] Preferred: {top_hooks[:3]} | Avoid: {worst_hooks}")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ALERT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

def _alert(alert_type: str, message: str, priority: str = "normal"):
    """Write alert to vault and attempt to insert into dashboard DB."""
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = NOW.strftime("%Y-%m-%d_%H%M")
    path = ALERTS_DIR / f"{ts}_{alert_type}.md"
    path.write_text(
        f"---\ntype: {alert_type}\npriority: {priority}\ndate: {ts}\n"
        f"agent: evolution_engine\n---\n\n## ALERTA: {alert_type}\n\n"
        f"**Prioridad:** {priority}\n\n{message}\n",
        encoding="utf-8",
    )
    # Also try to insert into dashboard feedback table for visibility
    try:
        con = sqlite3.connect(str(DB))
        con.execute(
            "INSERT INTO user_feedback (type, priority, message, context, status, agent_assigned) "
            "VALUES (?,?,?,?,?,?)",
            ("alerta", priority, message, alert_type, "pendiente", "A3+A8"),
        )
        con.commit()
        con.close()
    except Exception:
        pass
    print(f"  [ALERT] {priority.upper()}: {alert_type} — {message[:80]}")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. EVOLUTION LOG
# ═══════════════════════════════════════════════════════════════════════════════

def log_evolution(strat: dict, changes_summary: str):
    """Append to the evolution log in the strategy file."""
    version = strat.get("version", 0) + 1
    strat["version"] = version
    log = strat.setdefault("evolution_log", [])
    log.append({
        "version": version,
        "date": TODAY.isoformat(),
        "changes": changes_summary,
        "trigger": "autonomous_cycle",
    })
    # Keep only last 30 entries
    if len(log) > 30:
        strat["evolution_log"] = log[-30:]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print(f"\n{'='*60}")
    print(f"EVOLUTION ENGINE — {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Day {DAYS_ELAPSED}/{GOAL_DAYS} | {DAYS_REMAINING} days remaining")
    print(f"{'='*60}")

    if not DB.exists():
        # La DB de métricas (dashboard/curioclip.db) es LOCAL y está gitignoreada,
        # por lo que en el runner cloud no existe: el motor no puede evolucionar sin
        # datos reales. Salir 0 (no es un fallo de CI) y dejar señal clara.
        # FIX REAL pendiente: exportar metrics_snapshot.json al repo o correr el
        # motor localmente donde vive la DB. Ver plan de remediación 2026-05-29.
        print("[SKIP] No metrics DB in this environment — evolution requires real "
              "TikTok metrics. Engine is a NO-OP until a data source is wired up.")
        return 0

    strat = load_strategy()
    con = connect()

    try:
        # 1. Growth tracking
        growth = track_growth(con, strat)

        # 2. Restriction detection
        detect_restrictions(con, strat)

        # 3. Evolve niche weights
        evolve_niche_weights(con, strat)

        # 4. Evolve production params
        evolve_production_params(con, strat)

        # 5. Log the evolution
        changes = (
            f"growth={growth['trajectory']}, "
            f"restrict={strat.get('restrictions',{}).get('shadowban_risk','?')}, "
            f"niches={len(strat.get('niche_weights',{}))} adjusted"
        )
        log_evolution(strat, changes)

        # 6. Save
        save_strategy(strat)
        print(f"\n[OK] Strategy v{strat['version']} saved → {STRATEGY.name}")

    finally:
        con.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
