"""Publica V5 en TikTok via Chrome Bridge.
Usa CDP raw para crear tab + Playwright connect_over_cdp con timeout corto para subir archivo."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, time, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
VIDEO = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_01_2026-05-06_a_2026-05-12" / "VIERNES" / "OUTPUT" / "V5_final.mp4"

CAPTION = """¿Sabias que puedes meter la mano en METAL LIQUIDO sin quemarte? 🔬

El efecto Leidenfrost crea una barrera de vapor que te protege por una fraccion de segundo.

La fisica es mas increible de lo que crees 🤯

⚠️ NO intentes esto en casa — solo dura milisegundos

¿Que otro experimento quieres ver? 👇

#ciencia #fisica #datoscuriosos #sabiasque #curioclip #experimento"""


def main():
    if not VIDEO.exists():
        print(f"[FAIL] Video no encontrado: {VIDEO}")
        return

    print(f"[OK] Video: {VIDEO} ({VIDEO.stat().st_size//1024} KB)")

    # 1. Connect via Playwright
    from playwright.sync_api import sync_playwright
    print("[CONNECT] Playwright connect_over_cdp...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222", timeout=15000)
        except Exception as e:
            print(f"[FAIL] {e}")
            print("[INFO] Si Playwright sigue colgando, reinicia Chrome:")
            print("  python -m src.bridge.chrome_bridge launch")
            return

        ctx = browser.contexts[0]
        # Buscar tab existente de upload o crear uno
        page = None
        for pg in ctx.pages:
            if "tiktok.com" in pg.url and ("upload" in pg.url or "tiktokstudio" in pg.url):
                page = pg
                break
        if not page:
            page = ctx.new_page()
            print("[NAV] tiktok.com/tiktokstudio/upload")
            page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=30000)
            time.sleep(8)

        page.bring_to_front()
        print(f"[OK] Page: {page.url}")

        # 2. Buscar input[type=file]
        print("[SEARCH] Buscando input file...")
        try:
            file_input = page.locator("input[type='file']").first
            file_input.wait_for(state="attached", timeout=15000)
            file_input.set_input_files(str(VIDEO))
            print(f"[OK] Archivo cargado: {VIDEO.name}")
        except Exception as e:
            print(f"[WARN] {e}")
            page.screenshot(path="tiktok_upload_state.png")
            print("[OK] Screenshot del estado actual: tiktok_upload_state.png")
            return

        # 3. Esperar a que la pagina procese el video
        print("[WAIT] Esperando 25s para que TikTok procese el video...")
        time.sleep(25)
        page.screenshot(path="tiktok_after_upload.png", full_page=False)
        print("[OK] Screenshot post-upload: tiktok_after_upload.png")

        # 4. Buscar el campo de caption con selectors robustos
        print("[CAPTION] Llenando caption...")
        CAPTION_SELECTORS = [
            ".DraftEditor-root [contenteditable='true']",
            "[contenteditable='true'][data-contents='true']",
            ".notranslate[contenteditable='true']",
            "[placeholder*='caption' i]",
            "[placeholder*='descripcion' i]",
            "[contenteditable='true']",
        ]
        caption_filled = False
        for selector in CAPTION_SELECTORS:
            try:
                field = page.locator(selector).first
                field.wait_for(state="visible", timeout=5000)
                field.scroll_into_view_if_needed()
                field.click()
                time.sleep(0.8)
                # Limpiar con triple-click (selecciona todo el texto del campo)
                field.click(click_count=3)
                page.keyboard.press("Delete")
                time.sleep(0.3)
                # Escribir el caption en chunks para evitar timeouts
                chunks = CAPTION.split("\n")
                for i, chunk in enumerate(chunks):
                    page.keyboard.type(chunk, delay=12)
                    if i < len(chunks) - 1:
                        page.keyboard.press("Shift+Enter")
                        time.sleep(0.1)
                time.sleep(1.5)
                # Verificar que se escribio algo
                filled = field.input_value() or field.inner_text()
                if filled and len(filled.strip()) > 10:
                    print(f"[OK] Caption llenado con selector: {selector}")
                    caption_filled = True
                    break
                else:
                    print(f"[RETRY] Selector {selector} no produjo texto, intentando siguiente...")
            except Exception as e:
                print(f"[TRY] {selector}: {e}")
                continue

        if not caption_filled:
            print("[WARN caption] No se pudo inyectar caption automaticamente.")
            print()
            print("=" * 60)
            print("ACCION MANUAL REQUERIDA — copia y pega este caption:")
            print("=" * 60)
            print(CAPTION)
            print("=" * 60)

        page.screenshot(path="tiktok_ready_to_post.png", full_page=False)
        print("[OK] LISTO PARA PUBLICAR — screenshot: tiktok_ready_to_post.png")
        print()
        print("==> Ahora SOLO necesitas: revisar la pagina en tu Chrome y dar click en POSTEAR.")


if __name__ == "__main__":
    main()
