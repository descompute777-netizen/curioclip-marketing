"""Publica V5 en TikTok end-to-end via CDP raw.
Usa Input.insertText en lugar de execCommand para evitar el crash de React.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, asyncio, urllib.request, urllib.parse, base64
from pathlib import Path
import websockets

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
VIDEO = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_01_2026-05-06_a_2026-05-12" / "VIERNES" / "OUTPUT" / "V5_final.mp4"

CAPTION = (
    "¿Sabias que puedes meter la mano en METAL LIQUIDO sin quemarte?\n"
    "El efecto Leidenfrost crea una barrera de vapor que te protege por una fraccion de segundo.\n"
    "La fisica es mas increible de lo que crees.\n"
    "NO intentes esto en casa - solo dura milisegundos.\n"
    "¿Que otro experimento quieres ver?\n"
    "#ciencia #fisica #datoscuriosos #sabiasque #curioclip #experimento"
)


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self.mid = 0

    async def send(self, method, params=None):
        self.mid += 1
        cur = self.mid
        await self.ws.send(json.dumps({"id": cur, "method": method, "params": params or {}}))
        while True:
            data = json.loads(await self.ws.recv())
            if data.get("id") == cur:
                if "error" in data:
                    print(f"  [CDP ERR] {method}: {data['error'].get('message','')[:120]}")
                return data.get("result", {})


async def screenshot(c, name):
    r = await c.send("Page.captureScreenshot", {"format": "png"})
    if "data" in r:
        with open(name, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        print(f"[OK] {name}")


async def keep_alive_wait(c, total_seconds, ping_every=8):
    """Espera enviando pings cada N segundos para evitar timeout del WS."""
    elapsed = 0
    while elapsed < total_seconds:
        await asyncio.sleep(min(ping_every, total_seconds - elapsed))
        elapsed += ping_every
        # Ping ligero al CDP
        try:
            await c.send("Runtime.evaluate", {"expression": "1", "returnByValue": True})
        except Exception:
            pass


async def main():
    if not VIDEO.exists():
        print(f"[FAIL] {VIDEO}"); return
    print(f"[OK] Video: {VIDEO.stat().st_size//1024} KB")

    # Crear nueva tab limpia para upload
    upload_url = "https://www.tiktok.com/tiktokstudio/upload?from=upload"
    req = urllib.request.Request(
        f"http://localhost:9222/json/new?{urllib.parse.quote(upload_url)}",
        method="PUT"
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        tab = json.loads(r.read())
    print(f"[OK] Tab nueva: {tab['id'][:16]}")

    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=64*1024*1024,
                                   ping_interval=5, ping_timeout=60) as ws:
        c = CDP(ws)
        await c.send("Page.enable")
        await c.send("DOM.enable")
        await c.send("Runtime.enable")
        await c.send("Target.activateTarget", {"targetId": tab["id"]})

        # 1. Esperar a que la pagina cargue
        print("[WAIT] 28s para render TikTok Studio...")
        await keep_alive_wait(c, 28)

        # 2. Subir archivo
        print("[UPLOAD] Buscando file input...")
        doc = await c.send("DOM.getDocument", {"depth": -1})
        nodes = await c.send("DOM.querySelectorAll", {
            "nodeId": doc["root"]["nodeId"],
            "selector": "input[type='file']"
        })
        if not nodes.get("nodeIds"):
            print("[FAIL] No file input")
            await screenshot(c, "tiktok_no_input.png")
            return

        # Encontrar el que acepta video
        for node_id in nodes["nodeIds"]:
            attrs = await c.send("DOM.getAttributes", {"nodeId": node_id})
            attr_list = attrs.get("attributes", [])
            attr_dict = dict(zip(attr_list[::2], attr_list[1::2]))
            if "video" in attr_dict.get("accept", ""):
                target = node_id
                break
        else:
            target = nodes["nodeIds"][0]

        await c.send("DOM.setFileInputFiles", {
            "files": [str(VIDEO)],
            "nodeId": target
        })
        print(f"[OK] Archivo seteado en nodeId {target}")

        # 3. Esperar procesamiento de video (TikTok valida + transcodifica)
        print("[WAIT] 35s para procesamiento del video...")
        await keep_alive_wait(c, 35)
        await screenshot(c, "tiktok_step1_uploaded.png")

        # 4. Cerrar dialog de content check si aparece
        print("[DIALOG] Cerrando content check si existe...")
        await c.send("Runtime.evaluate", {
            "expression": """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const close = btns.find(b => /Cancelar|Cerrar|Close|Skip/i.test(b.textContent));
                    if (close) { close.click(); return 'closed:'+close.textContent; }
                    return 'no_dialog';
                })()
            """,
            "returnByValue": True
        })
        await asyncio.sleep(2)

        # 5. Localizar y click en el campo de caption
        print("[CAPTION] Localizando y clickeando caption field...")
        focus_result = await c.send("Runtime.evaluate", {
            "expression": """
                (() => {
                    // Buscar el editor de caption (puede ser contenteditable o data-text)
                    const editors = document.querySelectorAll('[contenteditable="true"]');
                    let target = null;
                    for (const el of editors) {
                        // Skip los muy pequenos (probablemente otros campos)
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 200 && rect.height > 30) {
                            target = el;
                            break;
                        }
                    }
                    if (!target) return 'no_editor_found';
                    target.focus();
                    target.click();
                    // Limpiar contenido existente
                    const sel = window.getSelection();
                    const range = document.createRange();
                    range.selectNodeContents(target);
                    sel.removeAllRanges();
                    sel.addRange(range);
                    return 'focused:'+target.tagName+'|w='+target.getBoundingClientRect().width;
                })()
            """,
            "returnByValue": True
        })
        print(f"  {focus_result.get('result',{}).get('value','')}")
        await asyncio.sleep(1)

        # 6. Borrar contenido existente con Backspace/Delete
        for _ in range(3):
            await c.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete"})
            await c.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Delete"})
        await asyncio.sleep(0.5)

        # 7. Insertar caption usando Input.insertText (CDP nativo, no React-breaking)
        print("[CAPTION] Insertando caption con Input.insertText...")
        await c.send("Input.insertText", {"text": CAPTION})
        await asyncio.sleep(3)
        await screenshot(c, "tiktok_step2_caption.png")

        # 8. Buscar y click en boton POSTEAR / Publicar / Post
        print("[POST] Buscando boton de publicar...")
        post_result = await c.send("Runtime.evaluate", {
            "expression": """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const postBtn = btns.find(b => {
                        const t = b.textContent.trim();
                        return /^(Postear|Publicar|Post|Publish)$/i.test(t) && !b.disabled;
                    });
                    if (postBtn) {
                        postBtn.scrollIntoView({block:'center'});
                        return 'found:' + postBtn.textContent.trim() + '|disabled='+postBtn.disabled;
                    }
                    // Listar todos los botones para debug
                    return 'no_post_btn|all=' + btns.map(b=>b.textContent.trim()).filter(t=>t.length<30).join('|');
                })()
            """,
            "returnByValue": True
        })
        print(f"  {post_result.get('result',{}).get('value','')[:300]}")

        # 9. Click el boton (segundo paso, despues del scroll)
        click_result = await c.send("Runtime.evaluate", {
            "expression": """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const postBtn = btns.find(b => {
                        const t = b.textContent.trim();
                        return /^(Postear|Publicar|Post|Publish)$/i.test(t) && !b.disabled;
                    });
                    if (postBtn) { postBtn.click(); return 'clicked'; }
                    return 'no_btn';
                })()
            """,
            "returnByValue": True
        })
        print(f"[POST] {click_result.get('result',{}).get('value','')}")

        # 10. Esperar confirmacion + screenshot
        await asyncio.sleep(8)
        await screenshot(c, "tiktok_step3_posted.png")

        # 11. Verificar URL/title
        url_r = await c.send("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
        title_r = await c.send("Runtime.evaluate", {"expression": "document.title", "returnByValue": True})
        print(f"\n[URL FINAL] {url_r.get('result',{}).get('value','')}")
        print(f"[TITLE]     {title_r.get('result',{}).get('value','')}")


asyncio.run(main())
