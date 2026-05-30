"""
cdp_upload.py — Subida a TikTok: Playwright (estable) + CDPSession file-set (vence antibot).
================================================================================
EL TRUCO que vence el muro: el input[type=file] de TikTok bloquea
page.set_input_files de Playwright (antibot). Pero `DOM.setFileInputFiles` por
CDPSession setea el archivo en el nodo SIN chequeos de visibilidad → pasa.
El resto del flujo (procesar, caption, Continuar, Publicar) lo maneja Playwright,
que mantiene la página viva y auto-espera (mucho más robusto que JS por websocket).

Usa el Chrome del bridge (:9222) ya logueado en TikTok.

  python -m src.bridge.cdp_upload --test  <video.mp4>          # solo prueba el file-set
  python -m src.bridge.cdp_upload <video.mp4> "<caption>"       # sube y publica
"""
from __future__ import annotations
import sys, time
from pathlib import Path

CDP = "http://localhost:9222"
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload"


def _cdp_set_file(ctx, page, mp4: Path) -> int:
    """Setea el archivo vía CDP RAW (bypassa antibot). Devuelve # de inputs seteados."""
    client = ctx.new_cdp_session(page)
    doc = client.send("DOM.getDocument")
    qsa = client.send("DOM.querySelectorAll",
                      {"nodeId": doc["root"]["nodeId"], "selector": "input[type='file']"})
    n = 0
    for nid in qsa.get("nodeIds", []):
        try:
            client.send("DOM.setFileInputFiles", {"files": [str(mp4)], "nodeId": nid})
            n += 1
        except Exception as e:
            print(f"    nodo {nid}: {str(e)[:60]}")
    return n


def _has_error(page) -> bool:
    try:
        t = page.inner_text("body").lower()
        return ("algo salió mal" in t) or ("something went wrong" in t) or ("vuelve a cargar" in t)
    except Exception:
        return False


def upload(video_path: str, caption: str = "", do_publish: bool = False) -> dict:
    mp4 = Path(video_path).resolve()
    if not mp4.exists():
        return {"ok": False, "step": "file", "error": f"no existe {mp4}"}
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"ok": False, "step": "deps", "error": "playwright no instalado"}

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP)
        except Exception as e:
            return {"ok": False, "step": "connect", "error": f"sin Chrome :9222 ({e})"}
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        # REUSAR el tab de TikTok existente (el tab nuevo no carga la UI de upload igual)
        page = next((pg for pg in ctx.pages if "tiktok.com" in (pg.url or "")), None)
        if page is None:
            page = ctx.new_page()

        # ── file-set con reintentos (vence antibot + maneja 'algo salió mal') ──
        accepted = False
        for attempt in range(1, 4):
            print(f"[1] (intento {attempt}/3) abriendo /upload...")
            try:
                page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=60000)
            except Exception:
                pass
            found = False
            for _ in range(25):
                try:
                    if (page.evaluate("document.querySelectorAll(\"input[type='file']\").length") or 0) > 0:
                        found = True; break
                except Exception:
                    pass
                page.wait_for_timeout(2000)
            if not found:
                print("    input no apareció"); continue
            n = _cdp_set_file(ctx, page, mp4)
            print(f"[2-3] archivo seteado vía CDP en {n} input(s); esperando procesamiento...")
            outcome = "timeout"
            for _ in range(50):
                page.wait_for_timeout(2000)
                if _has_error(page):
                    outcome = "error"; break
                if page.locator("video").count() > 0:
                    page.wait_for_timeout(5000)
                    outcome = "error" if _has_error(page) else "ok"
                    break
            print(f"    intento {attempt}: {outcome}")
            if outcome == "ok":
                accepted = True; break
            page.wait_for_timeout(2000)
        if not accepted:
            page.close()
            return {"ok": False, "step": "video_processing",
                    "error": "✅ Antibot del INPUT vencido (TikTok acepta el archivo), pero el "
                             "procesamiento del video falla ('Algo salió mal') tras 3 intentos."}

        if not do_publish:
            page.close()
            return {"ok": True, "step": "file_accepted",
                    "message": "✅ file-set CDP RAW funcionó — TikTok aceptó y procesó el video."}

        # ── publicar: state-machine con locators robustos de Playwright ────────
        print("[5] flujo de publicación...")
        caption_done = False
        deadline = time.time() + 220
        while time.time() < deadline:
            page.wait_for_timeout(2000)
            if _has_error(page):
                page.close()
                return {"ok": False, "step": "processing_error", "error": "Algo salió mal al publicar"}
            if "/content" in page.url:
                break
            # 1) caption
            if not caption_done:
                ed = page.locator("[contenteditable='true'], div.public-DraftEditor-content, textarea").first
                try:
                    if ed.count() > 0 and ed.is_visible():
                        cur = (ed.inner_text() if ed.evaluate("e=>e.tagName") != "TEXTAREA" else ed.input_value()) or ""
                        if len(cur.strip()) <= 5:
                            ed.click()
                            page.keyboard.press("Control+A"); page.keyboard.press("Delete")
                            page.wait_for_timeout(300)
                            page.keyboard.type(caption, delay=8)
                        caption_done = True
                        print("    caption escrito")
                except Exception:
                    pass
            # 2) Continuar / Siguiente
            advanced = False
            for lbl in ("Continuar", "Siguiente", "Continue", "Next"):
                b = page.get_by_role("button", name=lbl, exact=True)
                try:
                    if b.count() > 0 and b.first.is_enabled():
                        b.first.click(); print(f"    → {lbl}"); advanced = True; break
                except Exception:
                    pass
            if advanced:
                continue
            # 3) Publicar (cuando caption listo)
            if caption_done:
                for lbl in ("Publicar", "Post", "Publish"):
                    b = page.get_by_role("button", name=lbl, exact=True)
                    try:
                        if b.count() > 0 and b.first.is_enabled():
                            b.first.click(); print(f"    → {lbl}")
                            page.wait_for_timeout(3000)
                            for cl in ("Publicar ahora", "Post now", "Publish now"):
                                cb = page.get_by_role("button", name=cl, exact=True)
                                if cb.count() > 0:
                                    try: cb.first.click()
                                    except Exception: pass
                            break
                    except Exception:
                        pass
                # esperar confirmación
                for _ in range(20):
                    page.wait_for_timeout(2000)
                    if "/content" in page.url:
                        break
                break
        published = "/content" in page.url
        page.close()
        return {"ok": published, "step": "published" if published else "incomplete",
                "message": "✅ PUBLICADO vía CDP RAW (antibot vencido)" if published
                           else "no se confirmó la publicación (revisar TikTok Studio)"}


def main():
    args = sys.argv[1:]
    test = "--test" in args
    args = [a for a in args if a != "--test"]
    if not args:
        print(__doc__); return
    res = upload(args[0], args[1] if len(args) > 1 else "", do_publish=not test)
    print("\nRESULTADO:", res)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
