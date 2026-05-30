#!/usr/bin/env python3
"""
Upload Daemon — sube videos a TikTok automaticamente en su horario.

Se ejecuta como proceso de fondo. Cada 3 minutos revisa el schedule.
Cuando un video esta en su ventana de publicacion (+/- 10 min), lo sube.
Marca cada video como 'uploaded' en el JSON para no repetir.

Uso:
    python scripts/autonomous/upload_daemon.py          # foreground
    pythonw scripts/autonomous/upload_daemon.py         # background (sin ventana)

    Tambien se registra en Windows Task Scheduler via --install
"""
from __future__ import annotations
import sys, json, time, os, subprocess, logging
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_PATH = ROOT / "output_week_remaining" / "upload_schedule.json"
LOG_PATH = ROOT / "logs" / "upload_daemon.log"
PROFILE_DIR = Path.home() / "chrome-curioclip"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHECK_INTERVAL = 180  # seconds between schedule checks
UPLOAD_WINDOW_MINUTES = 15  # upload if within +/- this many minutes of scheduled time

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
# pythonw-safe: bajo pythonw sys.stdout es None → solo FileHandler en ese caso
_handlers = [logging.FileHandler(str(LOG_PATH), encoding="utf-8")]
if sys.stdout is not None:
    _handlers.append(logging.StreamHandler(sys.stdout))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_handlers,
)
log = logging.getLogger("upload_daemon")


def load_schedule() -> list[dict]:
    if not SCHEDULE_PATH.exists():
        return []
    return json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))


def save_schedule(schedule: list[dict]):
    SCHEDULE_PATH.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")


def is_due(entry: dict) -> bool:
    """Check if this video should be uploaded now."""
    if entry.get("status") == "uploaded":
        return False
    pub_str = entry.get("publish_at_utc", "")
    if not pub_str:
        return False
    try:
        pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
    except Exception:
        return False
    now = datetime.now(timezone.utc)
    delta = abs((now - pub_dt).total_seconds()) / 60
    return delta <= UPLOAD_WINDOW_MINUTES


def is_past_due(entry: dict) -> bool:
    """Check if we missed the window but should still upload (up to 2h late)."""
    if entry.get("status") == "uploaded":
        return False
    pub_str = entry.get("publish_at_utc", "")
    if not pub_str:
        return False
    try:
        pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
    except Exception:
        return False
    now = datetime.now(timezone.utc)
    diff_min = (now - pub_dt).total_seconds() / 60
    return UPLOAD_WINDOW_MINUTES < diff_min <= 120


CDP_PORT = 9222
CDP_URL = f"http://localhost:{CDP_PORT}"


def _is_chrome_cdp_running() -> bool:
    """Check if Chrome is running with debugging port open."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def _launch_chrome_cdp() -> bool:
    """Launch Chrome with remote debugging port to enable CDP attach."""
    if _is_chrome_cdp_running():
        return True
    try:
        log.info("Launching Chrome with CDP debugging port...")
        subprocess.Popen(
            [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                f"--remote-debugging-port={CDP_PORT}",
                f"--user-data-dir={PROFILE_DIR}",
                "--remote-allow-origins=*",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            shell=False,
        )
        # Wait for Chrome to be ready
        for _ in range(20):
            time.sleep(1)
            if _is_chrome_cdp_running():
                log.info(f"Chrome CDP ready at {CDP_URL}")
                return True
        log.error("Chrome CDP did not start within 20s")
        return False
    except Exception as e:
        log.error(f"Failed to launch Chrome: {e}")
        return False


def upload_to_tiktok(video_path: str, caption: str) -> bool:
    """Upload a single video to TikTok via Playwright CDP attach (anti-bot bypass)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.error("playwright not installed — run: pip install playwright")
        return False

    # Ensure Chrome is running with CDP open
    if not _launch_chrome_cdp():
        log.error("Chrome CDP not available — cannot upload")
        return False

    mp4 = Path(video_path)
    if not mp4.exists():
        log.error(f"Video file not found: {mp4}")
        return False

    log.info(f"Uploading {mp4.name} ({mp4.stat().st_size // 1024}KB)...")
    log.info(f"Caption: {caption[:80]}")

    try:
        with sync_playwright() as p:
            # Attach to existing Chrome via CDP (bypasses TikTok's bot detection)
            browser = p.chromium.connect_over_cdp(CDP_URL)
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.new_page()

            # Navigate to TikTok Studio upload - use generous timeouts since TikTok is slow
            try:
                page.goto("https://www.tiktok.com/tiktokstudio/upload",
                          wait_until="commit", timeout=90000)
                log.info(f"Navigation committed. URL: {page.url}")
            except Exception as nav_err:
                log.warning(f"Initial navigation slow ({nav_err}), continuing anyway...")

            # Wait for the actual page to load (look for upload UI)
            log.info("Waiting for upload UI to appear...")
            deadline_load = time.time() + 120
            page_loaded = False
            while time.time() < deadline_load:
                page.wait_for_timeout(3000)
                if page.locator("input[type='file']").count() > 0:
                    page_loaded = True
                    log.info("Upload UI ready")
                    break
                log.info(f"  ... still loading (URL: {page.url[:60]})")
            if not page_loaded:
                log.error("TikTok Studio upload UI never loaded after 120s")
                page.close()
                return False

            # Set file - force input visible via JS, then set_input_files
            log.info(f"Setting file: {mp4.name} ({mp4.stat().st_size//1024}KB)")
            file_set = False

            try:
                # Make all file inputs visible/enabled via JS so Playwright can use them
                page.evaluate("""
                    () => {
                        const inputs = document.querySelectorAll('input[type="file"]');
                        inputs.forEach(inp => {
                            inp.style.display = 'block';
                            inp.style.opacity = '1';
                            inp.style.visibility = 'visible';
                            inp.style.position = 'static';
                            inp.style.width = '300px';
                            inp.style.height = '40px';
                            inp.removeAttribute('hidden');
                            inp.removeAttribute('disabled');
                        });
                        return inputs.length;
                    }
                """)
                log.info("Forced file inputs to be visible")

                # Now set the file using page-level API (more robust)
                page.set_input_files("input[type='file']", str(mp4), timeout=30000)
                file_set = True
                log.info("File set successfully")
            except Exception as e:
                log.warning(f"Direct set_input_files failed: {str(e)[:150]}")

            if not file_set:
                # Last resort: try with file_chooser
                try:
                    log.info("Trying file_chooser approach...")
                    # Look for upload button to click
                    upload_btn = page.get_by_role("button", name="Select video to upload")
                    if upload_btn.count() == 0:
                        upload_btn = page.locator("button:has-text('Upload')").first
                    with page.expect_file_chooser(timeout=15000) as fc_info:
                        upload_btn.click(timeout=5000)
                    fc = fc_info.value
                    fc.set_files(str(mp4))
                    file_set = True
                    log.info("File set via file_chooser")
                except Exception as e:
                    log.error(f"file_chooser also failed: {str(e)[:150]}")

            if not file_set:
                log.error("All file upload strategies failed")
                page.close()
                return False

            log.info("File set, waiting for caption editor...")

            # Wait for caption editor
            deadline = time.time() + 180
            ce = None
            while time.time() < deadline:
                page.wait_for_timeout(3000)
                if page.locator("[contenteditable='true']").count() > 0:
                    ce = page.locator("[contenteditable='true']").first
                    break
            if not ce:
                log.error("Caption editor timeout")
                page.close()
                return False

            # Type caption
            page.wait_for_timeout(2000)
            ce.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Delete")
            page.wait_for_timeout(400)
            page.keyboard.type(caption, delay=10)
            page.wait_for_timeout(2000)

            # Click publish
            publish_btn = None
            for _ in range(5):
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
                page.wait_for_timeout(5000)

            if not publish_btn:
                log.error("Publish button not found")
                page.close()
                return False

            publish_btn.click()
            page.wait_for_timeout(3000)

            # Handle "Post now" confirmation if it appears
            for _ in range(5):
                for lbl in ("Publicar ahora", "Post now", "Publish now"):
                    btn = page.get_by_role("button", name=lbl, exact=True)
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

            # Wait for confirmation
            page.wait_for_timeout(5000)
            for _ in range(15):
                if "/content" in page.url:
                    log.info(f"Published successfully → {page.url}")
                    page.close()
                    return True
                page.wait_for_timeout(2000)

            log.warning("No redirect confirmation, but upload may have succeeded")
            page.close()
            return True

    except Exception as e:
        log.error(f"Upload failed: {e}")
        return False


def run_daemon():
    log.info("=" * 50)
    log.info("UPLOAD DAEMON started")
    log.info(f"Schedule: {SCHEDULE_PATH}")
    log.info(f"Check interval: {CHECK_INTERVAL}s")
    log.info(f"Upload window: +/- {UPLOAD_WINDOW_MINUTES} min")
    log.info("=" * 50)

    while True:
        try:
            schedule = load_schedule()
            pending = [e for e in schedule if e.get("status") != "uploaded"]
            now_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")

            if not pending:
                # PERSISTE: no morir cuando la cola se vacía — el motor nuevo
                # añade más contenido y el daemon debe seguir sirviéndolo.
                log.info(f"[{now_utc}] cola vacía — esperando nuevo contenido del motor...")
                time.sleep(CHECK_INTERVAL)
                continue

            # Check for due videos
            for entry in schedule:
                if is_due(entry):
                    gid = entry["guion_id"]
                    log.info(f">>> TIME TO UPLOAD: {gid} — {entry['title'][:40]}")

                    success = upload_to_tiktok(entry["video_path"], entry["caption"])

                    if success:
                        entry["status"] = "uploaded"
                        entry["uploaded_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        save_schedule(schedule)
                        log.info(f"<<< {gid} uploaded successfully")

                        # Write to dashboard feedback for visibility
                        _notify_dashboard(gid, entry["title"])
                    else:
                        entry["status"] = "upload_failed"
                        save_schedule(schedule)
                        log.error(f"<<< {gid} upload FAILED")

                elif is_past_due(entry):
                    gid = entry["guion_id"]
                    log.warning(f">>> PAST DUE (catching up): {gid}")
                    success = upload_to_tiktok(entry["video_path"], entry["caption"])
                    if success:
                        entry["status"] = "uploaded"
                        entry["uploaded_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        save_schedule(schedule)
                        log.info(f"<<< {gid} uploaded (late)")
                        _notify_dashboard(gid, entry["title"])

            # Next check
            next_pending = [e for e in schedule if e.get("status") not in ("uploaded", "upload_failed")]
            if next_pending:
                next_time = min(e.get("publish_at_utc", "") for e in next_pending)
                log.info(f"[{now_utc}] {len(next_pending)} pending | next: {next_time[:16]}")

        except Exception as e:
            log.error(f"Daemon error: {e}")

        time.sleep(CHECK_INTERVAL)


def _notify_dashboard(guion_id: str, title: str):
    """Insert upload notification into dashboard DB."""
    import sqlite3
    db = ROOT / "dashboard" / "curioclip.db"
    if not db.exists():
        return
    try:
        con = sqlite3.connect(str(db))
        con.execute(
            "INSERT INTO user_feedback (type, priority, message, context, status, agent_assigned) "
            "VALUES (?,?,?,?,?,?)",
            ("alerta", "normal",
             f"Video {guion_id} subido exitosamente: {title[:60]}",
             f"upload_daemon/{guion_id}", "resuelto", "A6"),
        )
        con.commit()
        con.close()
    except Exception:
        pass


def install_task_scheduler():
    """Register this script in Windows Task Scheduler to run at system startup."""
    python = sys.executable
    script = str(Path(__file__).resolve())
    task_name = "CurioClip_UploadDaemon"

    cmd = (
        f'schtasks /Create /TN "{task_name}" /TR "\"{python}\" \"{script}\"" '
        f'/SC ONSTART /RU "{os.environ.get("USERNAME", "")}" /F'
    )
    log.info(f"Installing scheduled task: {task_name}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        log.info(f"Task '{task_name}' installed successfully")
    else:
        log.error(f"Failed to install task: {result.stderr}")
    return result.returncode == 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if "--install" in sys.argv:
        install_task_scheduler()
    else:
        run_daemon()
