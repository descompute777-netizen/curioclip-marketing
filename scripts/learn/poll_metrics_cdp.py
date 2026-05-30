"""
poll_metrics_cdp.py — Métricas REALES de TikTok vía el Chrome Bridge (CDP).
================================================================================
Hace el dashboard "vivo": lee TikTok Studio con la sesión real del usuario
(CDP :9222, sin re-login, evita el antibot de Playwright), extrae por post
vistas/likes/comentarios, y escribe a la DB del dashboard:
  - account_metrics_daily (total_views, posts_count, followers si disponible)
  - metrics_snapshots (por video, match por caption)

Uso:
  python scripts/learn/poll_metrics_cdp.py            # scrapea + escribe DB
  python scripts/learn/poll_metrics_cdp.py --dry      # solo imprime
"""
from __future__ import annotations
import os, sys, json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("CDP_TAB", "tiktok")

_EXTRACT_JS = r"""
(function(){
  function num(s){
    s=(s||"").trim().toUpperCase().replace(/\s/g,"");
    var mult=1;
    if(s.endsWith("K")){mult=1000;s=s.slice(0,-1);}
    else if(s.endsWith("M")){mult=1000000;s=s.slice(0,-1);}
    else if(s.endsWith("MIL")){mult=1000;s=s.slice(0,-3);}
    s=s.replace(/[.,](?=\d{3}\b)/g,"");      // separador de miles
    s=s.replace(",",".");                      // decimal europeo
    var n=parseFloat(s); return isNaN(n)?0:Math.round(n*mult);
  }
  var seen={}, out=[];
  document.querySelectorAll('a[href*="/video/"]').forEach(function(a){
    var href=a.getAttribute("href"); if(!href||seen[href]) return; seen[href]=1;
    var row=a;
    for(var k=0;k<8;k++){ if(!row.parentElement) break; row=row.parentElement;
      var t=row.innerText||""; if(t.includes("Todo el")||t.includes("Solo")||t.includes("Amigos")) break; }
    if(!row) return;
    var L=(row.innerText||"").split("\n").map(function(s){return s.trim();}).filter(Boolean);
    var pi=-1; for(var i=0;i<L.length;i++){ if(/^(Todo el|Solo|Amigos|Seguidores)/.test(L[i])){pi=i;break;} }
    if(pi<0||pi+3>=L.length) return;
    out.push({href:href, duration:L[0]||"", caption:L[1]||"", date:L[2]||"",
              views:num(L[pi+1]), likes:num(L[pi+2]), comments:num(L[pi+3])});
  });
  return JSON.stringify(out);
})()
"""


def scrape() -> list[dict]:
    from src.bridge.cdp_drive import get_ws, cdp, js
    ws = get_ws("tiktok")
    if not ws:
        return []
    cdp(ws, "Page.enable"); cdp(ws, "Runtime.enable")
    cur = js(ws, "location.href") or ""
    if "tiktokstudio/content" not in cur:
        cdp(ws, "Page.navigate", {"url": "https://www.tiktok.com/tiktokstudio/content"})
        import time; time.sleep(7)
    raw = js(ws, _EXTRACT_JS)
    ws.close()
    try:
        return json.loads(raw) if raw else []
    except Exception:
        return []


def write_db(rows: list[dict]) -> dict:
    from dashboard import db
    db.init_db()
    acc = db.query_one("SELECT id FROM accounts WHERE handle='fugamental28' AND platform='tiktok'")
    acc_id = acc["id"] if acc else db.execute(
        "INSERT INTO accounts (name, handle, platform, niche) VALUES ('CurioClip','fugamental28','tiktok','curiosidades')")
    today = datetime.date.today().isoformat()
    total_views = sum(r["views"] for r in rows)
    posts = len(rows)
    # account_metrics_daily (upsert)
    db.execute(
        """INSERT INTO account_metrics_daily (account_id, date, total_views, posts_count)
           VALUES (?,?,?,?)
           ON CONFLICT(account_id, date) DO UPDATE SET total_views=excluded.total_views,
             posts_count=excluded.posts_count""",
        (acc_id, today, total_views, posts))
    db.execute("UPDATE accounts SET views_total=? WHERE id=?", (total_views, acc_id))
    # per-post metrics → match a videos por caption
    matched = 0
    now = db.now_iso()
    vids = db.query("SELECT id, caption, video_code FROM videos WHERE account_id=?", (acc_id,))
    for r in rows:
        cap = (r["caption"] or "").lower()
        hit = None
        for v in vids:
            vc = (v["caption"] or "").lower()
            key = (vc[:25] or v["video_code"] or "").lower()
            if key and key in cap:
                hit = v; break
        if not hit:
            continue
        last = db.query_one(
            "SELECT views FROM metrics_snapshots WHERE video_id=? ORDER BY captured_at DESC LIMIT 1",
            (hit["id"],))
        if last and last["views"] == r["views"]:
            continue
        db.execute(
            """INSERT INTO metrics_snapshots (video_id, views, likes, comments, captured_at)
               VALUES (?,?,?,?,?)""",
            (hit["id"], r["views"], r["likes"], r["comments"], now))
        matched += 1
    return {"posts_scraped": posts, "total_views": total_views,
            "metrics_matched": matched, "account_id": acc_id, "date": today}


def main(dry: bool = False) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rows = scrape()
    print(f"[POLL] {len(rows)} posts leídos de TikTok Studio (sesión real)")
    for r in rows[:8]:
        print(f"  {r['views']:>6} vistas {r['likes']:>4} likes {r['comments']:>3} com | {r['caption'][:46]}")
    if dry:
        print(f"[DRY] total_views_visibles={sum(r['views'] for r in rows)}")
        return 0
    res = write_db(rows)
    print(f"[POLL] DB: {res}")
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry" in sys.argv))
