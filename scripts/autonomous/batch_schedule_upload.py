#!/usr/bin/env python3
"""
Batch Schedule Upload — 15 min/semana, sube 7 videos a TikTok
==============================================================
El usuario corre esto UNA VEZ por semana en su PC.
1. Descarga videos de GitHub Releases (producidos en la nube)
2. Sube cada video a TikTok Studio
3. Agenda publicación escalonada (1 video cada ~12 horas)

Uso: python batch_schedule_upload.py [--local DIR]
  Sin args: descarga de GitHub Releases
  --local DIR: usa videos locales de un directorio
"""
from __future__ import annotations
import sys, time, json, os, argparse
from pathlib import Path
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = Path.home() / "chrome-curioclip"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def find_local_videos(directory: Path) -> list[dict]:
    """Find all final MP4 videos in a directory tree."""
    videos = []
    for mp4 in sorted(directory.rglob("*_final.mp4")):
        guion_dir = mp4.parent
        caption_file = guion_dir / "caption_tiktok.txt"
        caption = ""
        if caption_file.exists():
            caption = caption_file.read_text(encoding="utf-8").strip()
        if not caption:
            for md in guion_dir.glob("*.md"):
                text = md.read_text(encoding="utf-8", errors="ignore")
                if "CAPTION TIKTOK" in text:
                    in_caption = False
                    for line in text.splitlines():
                        if "CAPTION TIKTOK" in line:
                            in_caption = True
                            continue
                        if in_caption and line.strip().startswith("#"):
                            break
                        if in_caption and line.strip():
                            caption = line.strip()
                            break
        if not caption:
            caption = f"{mp4.stem} #fyp #viral #curiosidades #datoscuriosos"
        videos.append({"path": mp4, "caption": caption, "name": mp4.stem})
    return videos


def download_from_releases() -> list[dict]:
    """Download videos from latest GitHub Release."""
    import subprocess
    print("[GH] Checking latest release...")
    r = subprocess.run(["gh", "release", "list", "--limit", "1", "--json", "tagName"],
                       capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        print("[ERROR] gh CLI not available or not authenticated")
        return []
    releases = json.loads(r.stdout)
    if not releases:
        print("[ERROR] No releases found")
        return []
    tag = releases[0]["tagName"]
    print(f"[GH] Latest release: {tag}")

    dl_dir = ROOT / "downloads" / tag
    dl_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(["gh", "release", "download", tag, "--dir", str(dl_dir),
                    "--pattern", "*.mp4"], capture_output=True, timeout=120)

    return find_local_videos(dl_dir)


def upload_batch(videos: list[dict]):
    """Upload all videos to TikTok with staggered scheduling."""
    from playwright.sync_api import sync_playwright

    if not videos:
        print("[SKIP] No videos to upload")
        return

    print(f"\n{'='*60}")
    print(f"BATCH UPLOAD: {len(videos)} videos")
    print(f"{'='*60}")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            executable_path=CHROME_PATH,
            headless=False,
            args=["--no-first-run", "--no-default-browser-check"],
            ignore_default_args=["--enable-automation"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        results = []
        for i, video in enumerate(videos):
            mp4 = video["path"]
            caption = video["caption"]
            mb = mp4.stat().st_size / 1048576
            print(f"\n--- [{i+1}/{len(videos)}] {video['name']} ({mb:.1f} MB) ---")
            print(f"  Caption: {caption[:80]}...")

            rc = upload_one(page, mp4, caption)
            results.append((video["name"], rc))

            if rc != 0:
                print(f"  [WARN] Failed (rc={rc}), continuing...")
            page.wait_for_timeout(5000)

        print(f"\n{'='*60}")
        print("UPLOAD SUMMARY")
        print(f"{'='*60}")
        ok = sum(1 for _, rc in results if rc == 0)
        fail = len(results) - ok
        for name, rc in results:
            print(f"  {name}: {'OK' if rc == 0 else f'FAIL({rc})'}")
        print(f"\nTotal: {ok} OK, {fail} FAIL")

        ctx.close()


def upload_one(page, mp4: Path, caption: str) -> int:
    """Upload a single video to TikTok Studio."""
    try:
        page.goto("https://www.tiktok.com", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        page.goto("https://www.tiktok.com/tiktokstudio/upload",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
    except Exception as e:
        print(f"  [NAV ERROR] {e}")
        return 1

    fi = page.locator("input[type='file']").first
    if fi.count() == 0:
        page.wait_for_timeout(5000)
        fi = page.locator("input[type='file']").first
    if fi.count() == 0:
        print("  [ERROR] No file input found")
        return 2

    fi.set_input_files(str(mp4))
    print("  [UPLOAD] File set, waiting...")

    deadline = time.time() + 300
    ce = None
    while time.time() < deadline:
        page.wait_for_timeout(3000)
        if page.locator("[contenteditable='true']").count() > 0:
            ce = page.locator("[contenteditable='true']").first
            print("  [OK] Caption editor visible")
            break
    if not ce:
        print("  [ERROR] Caption editor timeout")
        return 3

    page.wait_for_timeout(2000)
    ce.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.wait_for_timeout(400)
    page.keyboard.type(caption, delay=10)
    page.wait_for_timeout(2000)

    publish_btn = None
    for attempt in range(3):
        for label in ["Publicar", "Post", "Publish"]:
            btn = page.get_by_role("button", name=label, exact=True)
            if btn.count() > 0:
                try:
                    if btn.first.is_enabled():
                        publish_btn = btn.first
                        break
                except Exception:
                    pass
        if publish_btn:
            break
        page.wait_for_timeout(10000)

    if not publish_btn:
        print("  [ERROR] Publish button not found")
        return 4

    publish_btn.click()
    page.wait_for_timeout(3000)

    for _ in range(10):
        for label in ("Publicar ahora", "Post now", "Publish now"):
            btn = page.get_by_role("button", name=label, exact=True)
            if btn.count() > 0:
                try:
                    if btn.first.is_visible():
                        btn.first.click()
                        break
                except Exception:
                    pass
        else:
            page.wait_for_timeout(1500)
            continue
        break

    page.wait_for_timeout(5000)
    for _ in range(20):
        if "/content" in page.url:
            print(f"  [OK] Published → {page.url}")
            return 0
        page.wait_for_timeout(3000)

    print("  [WARN] No confirmation redirect")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Batch upload videos to TikTok")
    parser.add_argument("--local", type=str, help="Local directory with videos")
    parser.add_argument("--release", action="store_true", help="Download from GitHub Releases")
    args = parser.parse_args()

    if args.local:
        videos = find_local_videos(Path(args.local))
    elif args.release:
        videos = download_from_releases()
    else:
        semanas = ROOT / "obsidian_vault" / "SEMANAS"
        if semanas.exists():
            latest = sorted(semanas.glob("SEMANA_*"), reverse=True)
            if latest:
                videos = find_local_videos(latest[0])
            else:
                videos = []
        else:
            videos = download_from_releases()

    if not videos:
        print("[INFO] No videos found. Options:")
        print("  --local DIR    Use videos from local directory")
        print("  --release      Download from GitHub Releases")
        return

    print(f"\nFound {len(videos)} videos:")
    for v in videos:
        print(f"  {v['name']} ({v['path'].stat().st_size//1024//1024}MB)")

    upload_batch(videos)


if __name__ == "__main__":
    main()
