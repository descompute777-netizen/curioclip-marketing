"""Upload BATCH_CLONE_01 videos (VC1-VC5) to TikTok via persistent browser context."""
from __future__ import annotations
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / "obsidian_vault" / "30_Contenido" / "BATCH_CLONE_01"
PROFILE_DIR = Path.home() / "chrome-curioclip"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CAPTIONS = {
    "VC1": "¿Que pasaria si abrieras un HOSPITAL en la antigua GRECIA? 🏛️⚕️ Te convertirias en un DIOS #SabiasQue #curiosidades #fyp #viral #datoscuriosos #historia #medicina",
    "VC2": "¿Que usaba la gente ANTES de que existiera el JABON? 🧼😱 La respuesta es PEOR de lo que imaginas #SabiasQue #curiosidades #fyp #viral #historia #higiene #datoscuriosos",
    "VC3": "Esto es lo que le pasa a tu cuerpo cuando NO DUERMES en 72 horas 😱🧠 A las 48h empiezan las ALUCINACIONES #ciencia #cuerpohumano #fyp #viral #salud #datoscuriosos #SabiasQue #nodormir",
    "VC4": "La temperatura EXACTA a la que tu cuerpo DEJA de funcionar 🌡️💀 Solo 16 grados entre VIVIR y MORIR #ciencia #cuerpohumano #fyp #viral #temperatura #datoscuriosos #SabiasQue",
    "VC5": "¿Como se lavaban los DIENTES antes del cepillo? 🦷😱 Los romanos usaban ORINA como enjuague bucal #SabiasQue #curiosidades #fyp #viral #historia #dientes #datoscuriosos #asqueroso",
}


def shot(page, name: str):
    p = ROOT / f"upload_{name}.png"
    page.screenshot(path=str(p), full_page=False)
    print(f"    [shot] {p.name}")


def upload_one(page, vc: str) -> int:
    mp4 = BATCH / vc / "final_video.mp4"
    if not mp4.exists():
        print(f"[ABORT {vc}] no existe final_video.mp4")
        return 1
    caption = CAPTIONS.get(vc, f"Curiosidad increible #{vc} #fyp #viral")
    mb = mp4.stat().st_size / 1048576
    print(f"\n{'='*60}\n  UPLOAD {vc}  ({mb:.1f} MB)\n{'='*60}")
    print(f"  caption: {caption[:100]}...")

    print("[NAV] TikTok Studio upload page")
    page.goto("https://www.tiktok.com/tiktokstudio/upload",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    shot(page, f"{vc}_01_arrived")

    fi = page.locator("input[type='file']").first
    if fi.count() == 0:
        print("[ABORT] no encontre input[type=file]")
        return 2
    print("[UPLOAD] setInputFiles...")
    fi.set_input_files(str(mp4))
    print("[UPLOAD] archivo seteado, esperando procesamiento...")

    deadline = time.time() + 180
    ce = None
    last_print = 0
    while time.time() < deadline:
        page.wait_for_timeout(2000)
        cnt = page.locator("[contenteditable='true']").count()
        if cnt > 0:
            ce = page.locator("[contenteditable='true']").first
            print("  [tick] caption editor visible")
            break
        elapsed = int(180 - (deadline - time.time()))
        if elapsed - last_print >= 10:
            print(f"  [tick] esperando upload... t={elapsed}s")
            last_print = elapsed
    if not ce:
        shot(page, f"{vc}_02_timeout")
        print("[ABORT] timeout esperando caption editor")
        return 3
    page.wait_for_timeout(2000)
    shot(page, f"{vc}_02_uploaded")

    ce.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.wait_for_timeout(400)

    print("[CAPTION] typing...")
    page.keyboard.type(caption, delay=10)
    page.wait_for_timeout(1500)
    shot(page, f"{vc}_03_caption")

    publish_btn = None
    for label in ["Publicar", "Post", "Publish"]:
        btn = page.get_by_role("button", name=label, exact=True)
        if btn.count() > 0:
            try:
                if btn.first.is_enabled():
                    publish_btn = btn.first
                    print(f"[BTN] '{label}' habilitado")
                    break
            except Exception:
                pass
    if not publish_btn:
        for label in ["Publicar", "Post", "Publish"]:
            loc = page.locator(f"button:has-text('{label}')")
            if loc.count() > 0:
                try:
                    if loc.first.is_enabled():
                        publish_btn = loc.first
                        print(f"[BTN] fallback '{label}' habilitado")
                        break
                except Exception:
                    pass
    if not publish_btn:
        print("[WAIT] Publicar aun no habilitado, espera 20s mas...")
        page.wait_for_timeout(20000)
        for label in ["Publicar", "Post", "Publish"]:
            btn = page.get_by_role("button", name=label, exact=True)
            if btn.count() > 0:
                try:
                    if btn.first.is_enabled():
                        publish_btn = btn.first
                        print(f"[BTN] '{label}' habilitado (despues de wait)")
                        break
                except Exception:
                    pass
    if not publish_btn:
        shot(page, f"{vc}_04_no_publish_btn")
        print("[ABORT] no encontre boton Publicar habilitado")
        return 4

    print("[CLICK] Publicar")
    publish_btn.click()
    page.wait_for_timeout(3000)
    shot(page, f"{vc}_05_after_publish")

    modal_deadline = time.time() + 20
    modal_clicked = False
    while time.time() < modal_deadline:
        for label in ("Publicar ahora", "Post now", "Publish now"):
            btn = page.get_by_role("button", name=label, exact=True)
            if btn.count() > 0:
                try:
                    if btn.first.is_visible() and btn.first.is_enabled():
                        print(f"[MODAL] click '{label}'")
                        btn.first.click()
                        modal_clicked = True
                        break
                except Exception:
                    pass
        if modal_clicked:
            break
        page.wait_for_timeout(1500)
    if not modal_clicked:
        print("[MODAL] no aparecio (publicacion directa probable)")
    page.wait_for_timeout(3000)
    shot(page, f"{vc}_05b_after_modal")

    deadline = time.time() + 90
    confirmed = False
    while time.time() < deadline:
        url = page.url
        try:
            body = page.evaluate("() => document.body.innerText.slice(0, 800)")
        except Exception:
            body = ""
        for kw in ("Publicado", "Posted", "Tu video se publico", "Procesando",
                   "tiktokstudio/content", "esta en proceso", "publicarse pronto",
                   "Tu publicacion", "se publico", "publicaciones"):
            if kw in body:
                print(f"  [confirm] match='{kw}'")
                confirmed = True
                break
        if "/content" in url or url.endswith("/tiktokstudio") or "tiktokstudio/posts" in url:
            print(f"  [confirm] navigation a {url}")
            confirmed = True
            break
        if confirmed:
            break
        page.wait_for_timeout(2000)
    shot(page, f"{vc}_06_final")
    print(f"[RESULT] {vc} confirmed={confirmed}  url={page.url}")
    return 0 if confirmed else 5


def main(codes: list[str]):
    print(f"Profile: {PROFILE_DIR} (existe={PROFILE_DIR.exists()})")
    print(f"Videos: {codes}")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            executable_path=CHROME_PATH,
            headless=False,
            args=["--no-first-run", "--no-default-browser-check"],
            ignore_default_args=["--enable-automation"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            results = []
            for code in codes:
                rc = upload_one(page, code)
                results.append((code, rc))
                if rc != 0:
                    print(f"\n[WARN] {code} no completo (rc={rc}). Continuo con siguiente.")
                page.wait_for_timeout(5000)
            print(f"\n{'='*60}")
            print("RESUMEN UPLOAD BATCH_CLONE_01")
            print(f"{'='*60}")
            for c, rc in results:
                status = "OK" if rc == 0 else f"FAIL(rc={rc})"
                print(f"  {c}  {status}")
            return 0 if all(rc == 0 for _, rc in results) else 1
        finally:
            print("\n[CLEANUP] cerrando contexto...")
            ctx.close()


if __name__ == "__main__":
    codes = sys.argv[1:] if len(sys.argv) > 1 else ["VC1", "VC2", "VC3", "VC4", "VC5"]
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main(codes))
