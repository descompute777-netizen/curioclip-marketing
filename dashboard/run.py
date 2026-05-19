"""
Launcher: pip-installs deps if missing, seeds DB, opens browser, runs uvicorn.

Usage:  python -m dashboard.run
        python -m dashboard.run --no-browser
        python -m dashboard.run --port 8080
"""
import argparse
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

REQUIRED = ["fastapi", "uvicorn", "jinja2", "python-multipart", "pydantic"]


def ensure_deps():
    missing = []
    for pkg in REQUIRED:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[INSTALL] {' '.join(missing)}")
        subprocess.run([sys.executable, "-m", "pip", "install", *missing, "-q"], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-seed", action="store_true")
    args = parser.parse_args()

    ensure_deps()

    from dashboard import db
    db.init_db()

    if not args.no_seed:
        from dashboard.seed import seed_all
        print("[SEED] Poblando desde obsidian_vault...")
        result = seed_all()
        print(f"[SEED] {result}")

    if not args.no_browser:
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(f"http://{args.host}:{args.port}")
        import threading
        threading.Thread(target=open_browser, daemon=True).start()

    print(f"\n{'='*60}\nCurioClip Mission Control\n  http://{args.host}:{args.port}\n{'='*60}\n")

    import uvicorn
    uvicorn.run("dashboard.app:app", host=args.host, port=args.port, reload=False, log_level="info")


if __name__ == "__main__":
    main()
