#!/usr/bin/env python3
"""
cloud_publish.py — Publica UN video a TikTok via Composio (100% cloud).

Flujo:
  1. Lee upload_schedule.json del repo
  2. Encuentra el video que corresponde a este horario (+/- 20 min)
  3. Descarga el MP4 de GitHub Releases
  4. Publica via Composio Content Posting API
  5. Marca como 'uploaded' en el schedule
  6. El workflow de GitHub Actions commitea el cambio

Uso (GitHub Actions):
    python scripts/autonomous/cloud_publish.py

Env vars:
    COMPOSIO_API_KEY  (requerido)
    GITHUB_TOKEN      (para descargar release assets)
"""
from __future__ import annotations
import os, sys, json, time, tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_PATH = ROOT / "output_week_remaining" / "upload_schedule.json"
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
RELEASE_TAG = "week-28-2026-05-28"
REPO = "descompute777-netizen/curioclip-marketing"
UPLOAD_WINDOW_MINUTES = 20
USER_ID = "curioclip"

sys.stdout.reconfigure(encoding="utf-8")


def load_schedule() -> list[dict]:
    if not SCHEDULE_PATH.exists():
        print("[ERROR] Schedule not found")
        return []
    return json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))


def save_schedule(schedule: list[dict]):
    SCHEDULE_PATH.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")


def find_due_video(schedule: list[dict]) -> dict | None:
    """Find the video that should be published right now."""
    now = datetime.now(timezone.utc)
    best = None
    best_delta = float("inf")

    for entry in schedule:
        if entry.get("status") in ("uploaded", "upload_failed"):
            continue
        pub_str = entry.get("publish_at_utc", "")
        if not pub_str:
            continue
        try:
            pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
        except Exception:
            continue

        delta_min = abs((now - pub_dt).total_seconds()) / 60

        # Within window and closest to scheduled time
        if delta_min <= UPLOAD_WINDOW_MINUTES and delta_min < best_delta:
            best = entry
            best_delta = delta_min

    # Also check past-due (up to 3h late) — catch up missed slots
    if not best:
        for entry in schedule:
            if entry.get("status") in ("uploaded", "upload_failed"):
                continue
            pub_str = entry.get("publish_at_utc", "")
            if not pub_str:
                continue
            try:
                pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            except Exception:
                continue
            delta_min = (now - pub_dt).total_seconds() / 60
            if 0 < delta_min <= 180:  # past due up to 3h
                if delta_min < best_delta:
                    best = entry
                    best_delta = delta_min

    return best


def download_from_release(guion_id: str, dest_dir: Path) -> Path | None:
    """Download video from GitHub Release."""
    import urllib.request
    filename = f"{guion_id}_final.mp4"
    dest = dest_dir / filename

    # Get asset download URL via GitHub API
    api_url = f"https://api.github.com/repos/{REPO}/releases/tags/{RELEASE_TAG}"
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            release = json.loads(r.read())
    except Exception as e:
        print(f"[ERROR] Cannot fetch release: {e}")
        return None

    asset_url = None
    for asset in release.get("assets", []):
        if asset["name"] == filename:
            asset_url = asset["browser_download_url"]
            break

    if not asset_url:
        print(f"[ERROR] Asset {filename} not found in release {RELEASE_TAG}")
        return None

    print(f"[DL] {asset_url}")
    dl_req = urllib.request.Request(asset_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(dl_req, timeout=120) as r:
        with open(dest, "wb") as f:
            while chunk := r.read(65536):
                f.write(chunk)

    if dest.stat().st_size > 100000:
        print(f"[DL] {dest.name} — {dest.stat().st_size // 1024}KB")
        return dest
    print(f"[ERROR] Downloaded file too small: {dest.stat().st_size}")
    return None


def publish_via_composio(video_path: Path, caption: str) -> dict:
    """Publish video to TikTok via Composio SDK."""
    try:
        from composio import Composio
    except ImportError:
        # Try composio-openai as fallback
        try:
            from composio_openai import Composio
        except ImportError:
            return {"ok": False, "error": "composio SDK not installed"}

    if not COMPOSIO_API_KEY:
        return {"ok": False, "error": "COMPOSIO_API_KEY not set"}

    client = Composio(api_key=COMPOSIO_API_KEY)

    # Check for active TikTok connection
    try:
        accounts = client.connected_accounts.list()
        items = accounts.items if hasattr(accounts, "items") else accounts
        active = None
        for a in items:
            tk = getattr(a, "toolkit", None)
            slug = getattr(tk, "slug", None) if tk else None
            if slug == "tiktok" and getattr(a, "status", "") == "ACTIVE":
                active = getattr(a, "user_id", USER_ID)
                break
        if not active:
            return {"ok": False, "error": "No active TikTok connection in Composio. Re-auth at composio.dev"}
    except Exception as e:
        return {"ok": False, "error": f"Connection check failed: {e}"}

    # Upload and publish
    print(f"[COMPOSIO] Publishing via user_id={active}...")
    try:
        resp = client.tools.execute(
            "TIKTOK_UPLOAD_VIDEO",
            user_id=active,
            arguments={
                "file_to_upload": {
                    "name": video_path.name,
                    "mimetype": "video/mp4",
                    "path": str(video_path.absolute()),
                },
                "publish": True,
                "caption": caption[:2200],
                "privacy_level": "PUBLIC_TO_EVERYONE",
            },
        )
    except Exception as e:
        return {"ok": False, "error": f"Upload exception: {e}"}

    raw = resp if isinstance(resp, dict) else (
        resp.model_dump() if hasattr(resp, "model_dump") else {"raw": str(resp)}
    )
    data = raw.get("data") or raw

    if raw.get("error") or data.get("error"):
        return {"ok": False, "error": str(raw.get("error") or data.get("error")), "raw": raw}

    publish_id = (data.get("publish_id")
                  or (data.get("response_data") or {}).get("publish_id"))

    if publish_id:
        # Poll for completion
        print(f"[COMPOSIO] publish_id={publish_id}, polling status...")
        for _ in range(60):
            time.sleep(5)
            try:
                sr = client.tools.execute(
                    "TIKTOK_FETCH_PUBLISH_STATUS",
                    user_id=active,
                    arguments={"publish_id": publish_id},
                )
                sraw = sr if isinstance(sr, dict) else (
                    sr.model_dump() if hasattr(sr, "model_dump") else {})
                sdata = sraw.get("data") or sraw
                status = (sdata.get("status")
                          or (sdata.get("response_data") or {}).get("status"))
                if status == "PUBLISH_COMPLETE":
                    return {"ok": True, "publish_id": publish_id, "status": status}
                if status in ("FAILED", "PUBLISH_FAILED"):
                    return {"ok": False, "publish_id": publish_id, "status": status,
                            "error": str(sdata.get("fail_reason", "failed"))}
            except Exception:
                continue

    return {"ok": True, "publish_id": publish_id, "status": "submitted", "raw": raw}


def main():
    print(f"\n{'='*50}")
    print(f"CLOUD PUBLISH — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}")

    schedule = load_schedule()
    if not schedule:
        return 0

    pending = [e for e in schedule if e.get("status") not in ("uploaded", "upload_failed")]
    print(f"Schedule: {len(pending)} pending / {len(schedule)} total")

    entry = find_due_video(schedule)
    if not entry:
        print("[SKIP] No video due right now")
        return 0

    gid = entry["guion_id"]
    caption = entry["caption"]
    print(f"\n[DUE] {gid} — {entry['title'][:50]}")
    print(f"  Scheduled: {entry['publish_at_utc']}")
    print(f"  Caption: {caption[:80]}")

    # Download from GitHub Release
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        video = download_from_release(gid, tmp_dir)
        if not video:
            entry["status"] = "download_failed"
            save_schedule(schedule)
            print("[FAIL] Could not download video")
            return 1

        # Publish via Composio
        result = publish_via_composio(video, caption)

    if result.get("ok"):
        entry["status"] = "uploaded"
        entry["uploaded_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry["publish_id"] = result.get("publish_id")
        save_schedule(schedule)
        print(f"\n[OK] {gid} published successfully!")
        return 0
    else:
        entry["status"] = "upload_failed"
        entry["error"] = result.get("error", "unknown")
        save_schedule(schedule)
        print(f"\n[FAIL] {gid}: {result.get('error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
