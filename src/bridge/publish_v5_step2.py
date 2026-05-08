"""Step 2: cierra dialog de content check y llena caption en TikTok upload."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, asyncio, urllib.request, base64
import websockets

CAPTION = """¿Sabias que puedes meter la mano en METAL LIQUIDO sin quemarte?
El efecto Leidenfrost crea una barrera de vapor que te protege por una fraccion de segundo. La fisica es mas increible de lo que crees.
NO intentes esto en casa - solo dura milisegundos
¿Que otro experimento quieres ver?
#ciencia #fisica #datoscuriosos #sabiasque #curioclip #experimento"""


async def find_tiktok_tab():
    with urllib.request.urlopen("http://localhost:9222/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in tabs:
        if t.get("type") == "page" and "tiktokstudio/upload" in t.get("url", ""):
            return t
    return None


async def cdp_send(ws, method, params=None, mid=[0]):
    mid[0] += 1
    cur = mid[0]
    await ws.send(json.dumps({"id": cur, "method": method, "params": params or {}}))
    while True:
        data = json.loads(await ws.recv())
        if data.get("id") == cur:
            return data.get("result", {})


async def main():
    tab = await find_tiktok_tab()
    if not tab:
        print("[FAIL] No se encontro tab de upload")
        return
    print(f"[OK] Tab: {tab['title'][:40]}")

    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=64*1024*1024) as ws:
        mid = [0]
        async def s(m, p=None): return await cdp_send(ws, m, p, mid)

        await s("Page.enable")
        await s("Runtime.enable")
        await s("Target.activateTarget", {"targetId": tab["id"]})

        # 1. Cerrar dialog de content check (clickear "Activar")
        print("[CDP] Cerrando dialog de content check...")
        await s("Runtime.evaluate", {
            "expression": """
                (() => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const activar = buttons.find(b => b.textContent.trim() === 'Activar');
                    const cancelar = buttons.find(b => b.textContent.trim() === 'Cancelar');
                    const target = activar || cancelar;
                    if (target) { target.click(); return target.textContent; }
                    return 'no_dialog';
                })()
            """,
            "returnByValue": True
        })
        await asyncio.sleep(2)

        # 2. Encontrar el campo de caption (es contenteditable)
        print("[CDP] Buscando campo de caption...")
        result = await s("Runtime.evaluate", {
            "expression": """
                (() => {
                    const el = document.querySelector('[data-text="true"]')
                            || document.querySelector('[contenteditable="true"]');
                    if (!el) return 'no_caption_field';
                    el.focus();
                    el.click();
                    return el.tagName + '|' + (el.getAttribute('data-text') || '') + '|' + el.outerHTML.slice(0,200);
                })()
            """,
            "returnByValue": True
        })
        print(f"[CDP] {result.get('result',{}).get('value','')[:200]}")
        await asyncio.sleep(1)

        # 3. Limpiar y escribir caption usando Input.dispatchKeyEvent
        # Mejor approach: usar execCommand selectAll + delete + insertText
        print("[CDP] Llenando caption...")
        caption_escaped = CAPTION.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        await s("Runtime.evaluate", {
            "expression": f"""
                (() => {{
                    const el = document.querySelector('[contenteditable="true"]');
                    if (!el) return 'no_field';
                    el.focus();
                    document.execCommand('selectAll', false);
                    document.execCommand('delete', false);
                    document.execCommand('insertText', false, `{caption_escaped}`);
                    return el.textContent.length + ' chars insertados';
                }})()
            """,
            "returnByValue": True
        })
        await asyncio.sleep(3)

        # 4. Screenshot final
        result = await s("Page.captureScreenshot", {"format": "png"})
        if "data" in result:
            with open("tiktok_ready_to_post.png", "wb") as f:
                f.write(base64.b64decode(result["data"]))
            print("[OK] Screenshot final: tiktok_ready_to_post.png")

        print()
        print("=" * 50)
        print("LISTO PARA PUBLICAR")
        print("=" * 50)
        print("Ve a tu Chrome, revisa el video y caption, y dale POSTEAR")


asyncio.run(main())
