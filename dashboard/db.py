"""
SQLite database layer for the dashboard.
- Schema defined inline (single source of truth)
- get_conn() returns a row-factory connection (dict-like rows)
- init_db() creates tables idempotently
- All queries are parameterized
"""
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "dashboard" / "curioclip.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  handle TEXT NOT NULL,
  platform TEXT NOT NULL,
  niche TEXT,
  status TEXT DEFAULT 'active',
  followers_current INTEGER DEFAULT 0,
  followers_goal INTEGER DEFAULT 10000,
  views_total INTEGER DEFAULT 0,
  notes TEXT,
  color TEXT DEFAULT '#fbbf24',
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(handle, platform)
);

CREATE TABLE IF NOT EXISTS videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  video_code TEXT,
  guion_id TEXT,
  title TEXT NOT NULL,
  hook TEXT,
  caption TEXT,
  hashtags TEXT,
  niche TEXT,
  duration_s REAL,
  file_path TEXT,
  thumbnail_path TEXT,
  status TEXT DEFAULT 'draft',
  vscore_predicted REAL,
  vscore_actual REAL,
  scheduled_at TEXT,
  published_at TEXT,
  external_id TEXT,
  external_url TEXT,
  hypothesis TEXT,
  outcome TEXT,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_videos_account ON videos(account_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_scheduled ON videos(scheduled_at);

CREATE TABLE IF NOT EXISTS metrics_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  views INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  shares INTEGER DEFAULT 0,
  saves INTEGER DEFAULT 0,
  retention_avg REAL,
  hook_rate REAL,
  follow_conversions INTEGER DEFAULT 0,
  captured_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_metrics_video ON metrics_snapshots(video_id, captured_at);

CREATE TABLE IF NOT EXISTS account_metrics_daily (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  date TEXT NOT NULL,
  followers INTEGER,
  total_views INTEGER,
  total_likes INTEGER,
  posts_count INTEGER,
  engagement_rate REAL,
  hook_rate REAL,
  UNIQUE(account_id, date)
);

CREATE TABLE IF NOT EXISTS simulations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  source TEXT,
  visualeyes_attention REAL,
  mirofish_spread REAL,
  mirofish_sentiment REAL,
  hook_score REAL,
  vscore_computed REAL,
  raw_json TEXT,
  captured_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS suggestions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_url TEXT,
  source_platform TEXT,
  title TEXT,
  description TEXT,
  view_count INTEGER,
  duration_s REAL,
  golden_start REAL,
  golden_end REAL,
  status TEXT DEFAULT 'inbox',
  score REAL,
  hook_extracted TEXT,
  niche TEXT,
  notes TEXT,
  added_by TEXT,
  added_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS automation_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent TEXT,
  action TEXT,
  account_id INTEGER REFERENCES accounts(id),
  payload TEXT,
  scheduled_for TEXT,
  status TEXT DEFAULT 'pending',
  result TEXT,
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_queue_status ON automation_queue(status, scheduled_for);

CREATE TABLE IF NOT EXISTS pipeline_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_type TEXT,
  account_id INTEGER REFERENCES accounts(id),
  status TEXT,
  log_path TEXT,
  metadata TEXT,
  started_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT
);

CREATE TABLE IF NOT EXISTS learn_patterns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pattern_type TEXT,
  pattern_value TEXT,
  account_id INTEGER REFERENCES accounts(id),
  sample_size INTEGER,
  avg_views REAL,
  avg_engagement REAL,
  confidence REAL,
  detected_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS calibration_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER REFERENCES accounts(id),
  sample_size INTEGER,
  mae REAL,
  rmse REAL,
  bias REAL,
  is_calibrated INTEGER DEFAULT 0,
  computed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS briefings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sprint_number INTEGER,
  date TEXT,
  status_summary TEXT,
  kpis_json TEXT,
  decisions TEXT,
  next_steps TEXT,
  blockers TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
"""


def get_conn() -> sqlite3.Connection:
    """Returns a connection with row factory and FK enforcement."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def cursor():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize schema. Safe to call multiple times."""
    with cursor() as c:
        c.executescript(SCHEMA)
    print(f"[DB] Schema initialized at {DB_PATH}")


def query(sql: str, params: tuple = ()) -> list[dict]:
    with cursor() as c:
        rows = c.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def query_one(sql: str, params: tuple = ()) -> dict | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: tuple = ()) -> int:
    """Returns lastrowid for INSERTs."""
    with cursor() as c:
        cur = c.execute(sql, params)
        return cur.lastrowid


def execute_many(sql: str, seq: Iterable[tuple]) -> None:
    with cursor() as c:
        c.executemany(sql, seq)


# Stats helpers ─────────────────────────────────────────────────────────────

def stats_overview() -> dict:
    """KPIs for the homepage."""
    with cursor() as c:
        # totals
        accs = c.execute("SELECT COUNT(*) n FROM accounts WHERE status='active'").fetchone()[0]
        vids = c.execute("SELECT COUNT(*) n FROM videos").fetchone()[0]
        pub = c.execute("SELECT COUNT(*) n FROM videos WHERE status='published'").fetchone()[0]
        sched = c.execute("SELECT COUNT(*) n FROM videos WHERE status='scheduled'").fetchone()[0]
        sugg = c.execute("SELECT COUNT(*) n FROM suggestions WHERE status='inbox'").fetchone()[0]
        queue = c.execute("SELECT COUNT(*) n FROM automation_queue WHERE status='pending'").fetchone()[0]
        # latest metrics
        views_7d = c.execute(
            """SELECT COALESCE(SUM(m.views), 0) FROM metrics_snapshots m
               WHERE m.captured_at >= datetime('now', '-7 days')"""
        ).fetchone()[0]
        followers_total = c.execute(
            "SELECT COALESCE(SUM(followers_current), 0) FROM accounts"
        ).fetchone()[0]
    return {
        "accounts_active": accs,
        "videos_total": vids,
        "videos_published": pub,
        "videos_scheduled": sched,
        "suggestions_inbox": sugg,
        "queue_pending": queue,
        "views_7d": views_7d,
        "followers_total": followers_total,
    }


def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)
