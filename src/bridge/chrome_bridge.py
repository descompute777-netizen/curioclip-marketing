"""
Chrome Bridge — CurioClip
==========================
Conecta a TU Chrome real (con tu sesión y cookies) via CDP attach.

Soluciona el bloqueo de Google/TikTok contra navegadores automatizados:
- Chrome se lanza por TI con --remote-debugging-port=9222
- TÚ navegas y te logueas normalmente (real user actions)
- Playwright se ATA al Chrome ya corriendo via connect_over_cdp
- Ningún sitio detecta automatización porque NO la hay en el lanzamiento

USO:
    1. python -m src.bridge.chrome_bridge launch
       → Lanza Chrome con debugging port. Loguéate normalmente.
    2. python -m src.bridge.chrome_bridge tabs
       → Lista pestañas que tienes abiertas.
    3. python -m src.bridge.chrome_bridge tiktok-analytics
       → Lee TikTok Studio analytics de tu pestaña activa.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

CDP_PORT = 9222
CDP_URL = f"http://localhost:{CDP_PORT}"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = Path.home() / "chrome-curioclip"


def is_chrome_running_cdp() -> bool:
    """Check if Chrome is running with debugging port open."""
    import urllib.request, urllib.error
    try:
        with urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def launch_chrome():
    """Launch Chrome with remote debugging on a dedicated profile."""
    if is_chrome_running_cdp():
        print(f"[OK] Chrome ya corriendo en CDP {CDP_URL}")
        return

    PROFILE_DIR.mkdir(exist_ok=True)
    args = [
        CHROME_PATH,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.tiktok.com/",
    ]
    print(f"Lanzando Chrome con debugging en puerto {CDP_PORT}...")
    print(f"Perfil dedicado: {PROFILE_DIR}")
    subprocess.Popen(args, shell=False)
    time.sleep(3)
    if is_chrome_running_cdp():
        print(f"[OK] Chrome operativo. Abre cualquier sitio y loguéate normalmente.")
        print(f"  La sesión se guarda en {PROFILE_DIR} para futuros usos.")
    else:
        print("[WARN] Chrome no respondió al puerto CDP. Revisar firewall/antivirus.")


def list_tabs():
    """List all tabs in user's Chrome via CDP."""
    if not is_chrome_running_cdp():
        print("[FAIL] Chrome no está corriendo con CDP. Ejecutar primero: launch")
        return
    import urllib.request
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    pages = [t for t in tabs if t.get("type") == "page"]
    print(f"\n[TABS] {len(pages)} pestaña(s) abierta(s):\n")
    for i, t in enumerate(pages, 1):
        print(f"  [{i}] {t.get('title', '(sin titulo)')[:60]}")
        print(f"      {t.get('url','')[:80]}")
    return pages


def get_page_content(url_filter: str = "tiktok.com"):
    """Get content from a specific tab using Playwright connect_over_cdp."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        target = None
        for page in context.pages:
            if url_filter in page.url:
                target = page
                break

        if not target:
            print(f"[FAIL] Ninguna pestaña con '{url_filter}'. Pestañas abiertas:")
            for p_ in context.pages:
                print(f"  - {p_.url}")
            return None

        print(f"[OK] Atado a pestaña: {target.url}")
        title = target.title()
        # Get text content
        content = target.evaluate("() => document.body.innerText")
        return {"url": target.url, "title": title, "content": content[:3000]}


def tiktok_analytics():
    """Extract TikTok Studio analytics from user's logged-in tab."""
    print("Buscando pestaña de TikTok Studio...")
    result = get_page_content("tiktokstudio")
    if not result:
        print("Abre TikTok Studio en tu Chrome primero: tiktok.com/tiktokstudio")
        return
    print(f"\n[ANALYTICS] Title: {result['title']}\n")
    print("Content extracted:\n")
    print(result["content"])


def screenshot_tab(url_filter: str, output: str = "tab_screenshot.png"):
    """Take a screenshot of a specific tab via CDP."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        for page in context.pages:
            if url_filter in page.url:
                page.screenshot(path=output, full_page=True)
                print(f"[OK] Screenshot: {output}")
                return output
        print(f"[FAIL] No se encontró pestaña con '{url_filter}'")


def main():
    parser = argparse.ArgumentParser(description="Chrome Bridge para CurioClip")
    parser.add_argument("action", choices=["launch", "tabs", "analytics", "screenshot", "content"])
    parser.add_argument("--url", default="tiktok.com", help="Filtro URL para acciones de pestaña")
    parser.add_argument("--out", default="tab_screenshot.png")
    args = parser.parse_args()

    if args.action == "launch":
        launch_chrome()
    elif args.action == "tabs":
        list_tabs()
    elif args.action == "analytics":
        tiktok_analytics()
    elif args.action == "screenshot":
        screenshot_tab(args.url, args.out)
    elif args.action == "content":
        result = get_page_content(args.url)
        if result:
            print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
