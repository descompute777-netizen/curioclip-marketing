"""Recovery: cierra dialog de cancelar, llena caption y postea correctamente."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, asyncio, urllib.request, base64
import websockets

CAPTION = (
    "Sabias que puedes meter la mano en METAL LIQUIDO sin quemarte? "
    "El efecto Leidenfrost crea una barrera de vapor que te protege por una fraccion de segundo. "
    "La fisica es mas increible de lo que crees. "
    "NO intentes esto en casa - solo dura milisegundos. "
    "Que otro experimento quieres ver? "
    "#ciencia #fisica #datoscuriosos #sabiasque #curioclip #experimento"
)


async def find_upload_tab():
    with urllib.request.urlopen("http://localhost:9222/json", timeout=5) as r:
        tabs = json.loads(r.read())
    # Buscar el tab de upload mas reciente
    upload_tabs = [t for t in tabs if t.get("type")=="page" and "tiktokstudio/upload" in t.get("url","")]
    if upload_tabs:
        return upload_tabs[0]
    return None


class CDP:
    def __init__(self, ws):
        self.ws = ws; self.mid = 0
    async def send(self, method, params=None):
        self.mid += 1; cur = self.mid
        await self.ws.send(json.dumps({"id":cur,"method":method,"params":params or {}}))
        while True:
            d = json.loads(await self.ws.recv())
            if d.get("id")==cur:
                if "error" in d: print(f"  [ERR {method}] {d['error'].get('message','')[:120]}")
                return d.get("result",{})


async def screenshot(c, name):
    r = await c.send("Page.captureScreenshot",{"format":"png"})
    if "data" in r:
        with open(name,"wb") as f: f.write(base64.b64decode(r["data"]))
        print(f"[OK] {name}")


async def keepalive(c, total):
    el = 0
    while el < total:
        await asyncio.sleep(min(6, total-el)); el += 6
        try: await c.send("Runtime.evaluate",{"expression":"1","returnByValue":True})
        except: pass


async def main():
    tab = await find_upload_tab()
    if not tab:
        print("[FAIL] no upload tab"); return
    print(f"[OK] Tab: {tab['id'][:16]}")

    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=64*1024*1024,
                                   ping_interval=5, ping_timeout=60) as ws:
        c = CDP(ws)
        await c.send("Page.enable")
        await c.send("Runtime.enable")
        await c.send("Target.activateTarget", {"targetId": tab["id"]})

        # 1. Cerrar dialog "¿Seguro que quieres cancelar?"  -> click "No"
        print("[1] Cerrando dialog de cancelar...")
        r = await c.send("Runtime.evaluate", {
            "expression": """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const noBtn = btns.find(b => b.textContent.trim() === 'No');
                    if (noBtn) { noBtn.click(); return 'clicked_No'; }
                    return 'no_dialog';
                })()
            """,
            "returnByValue": True
        })
        print(f"   {r.get('result',{}).get('value','')}")
        await asyncio.sleep(2)

        # 2. Esperar a que el video llegue a 100%
        print("[2] Esperando 20s para que video procese al 100%...")
        await keepalive(c, 20)
        await screenshot(c, "tiktok_recover_1.png")

        # 3. Localizar el campo de descripcion (el que tiene V5_final)
        print("[3] Localizando descripcion...")
        r = await c.send("Runtime.evaluate", {
            "expression": """
                (() => {
                    // El caption en TikTok Studio es un div contenteditable que contiene
                    // un span con data-text="true" mostrando el placeholder/texto
                    const editors = Array.from(document.querySelectorAll('[contenteditable="true"]'));
                    let target = null;
                    let info = [];
                    for (const el of editors) {
                        const r = el.getBoundingClientRect();
                        info.push(`${el.tagName}:w=${Math.round(r.width)}h=${Math.round(r.height)}`);
                        if (r.width > 300 && r.height > 30) { target = el; break; }
                    }
                    if (!target && editors.length) target = editors[0];
                    if (!target) return 'no_editor|info='+info.join(',');
                    target.focus();
                    target.click();
                    return 'focused:'+target.tagName+'|info='+info.join(',');
                })()
            """,
            "returnByValue": True
        })
        print(f"   {r.get('result',{}).get('value','')[:300]}")
        await asyncio.sleep(1)

        # 4. SelectAll + delete del placeholder/texto previo
        print("[4] Borrando contenido previo (Ctrl+A + Delete)...")
        await c.send("Input.dispatchKeyEvent", {"type":"keyDown","key":"a","modifiers":2})  # 2 = Ctrl
        await c.send("Input.dispatchKeyEvent", {"type":"keyUp","key":"a","modifiers":2})
        await asyncio.sleep(0.3)
        await c.send("Input.dispatchKeyEvent", {"type":"keyDown","key":"Delete"})
        await c.send("Input.dispatchKeyEvent", {"type":"keyUp","key":"Delete"})
        await asyncio.sleep(0.5)

        # 5. Insertar caption
        print("[5] Insertando caption con Input.insertText...")
        await c.send("Input.insertText", {"text": CAPTION})
        await asyncio.sleep(3)
        await screenshot(c, "tiktok_recover_2_caption.png")

        # 6. Buscar boton Publicar (el del bottom de la pagina, no el cancelar)
        print("[6] Localizando boton Publicar correcto...")
        r = await c.send("Runtime.evaluate", {
            "expression": """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    // Listar todos para debug
                    const all = btns.map(b => ({
                        text: b.textContent.trim().slice(0,30),
                        disabled: b.disabled,
                        bottom: b.getBoundingClientRect().bottom
                    })).filter(b => b.text.length > 0 && b.text.length < 30);
                    const candidates = all.filter(b =>
                        /^(Publicar|Postear|Post|Publish)$/i.test(b.text) && !b.disabled
                    );
                    return JSON.stringify({all: all.slice(0,30), candidates});
                })()
            """,
            "returnByValue": True
        })
        print(f"   {r.get('result',{}).get('value','')[:600]}")
        await asyncio.sleep(1)

        # 7. Click el boton Publicar mas cerca al bottom de la pagina
        print("[7] Click en Publicar (el del bottom)...")
        r = await c.send("Runtime.evaluate", {
            "expression": """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'))
                        .filter(b => /^(Publicar|Postear|Post|Publish)$/i.test(b.textContent.trim()) && !b.disabled);
                    if (!btns.length) return 'no_publicar';
                    // El boton mas abajo en la pagina = el correcto (los del header son cancel)
                    btns.sort((a,b) => b.getBoundingClientRect().top - a.getBoundingClientRect().top);
                    const target = btns[0];
                    target.scrollIntoView({block:'center'});
                    target.click();
                    return 'clicked|top='+Math.round(target.getBoundingClientRect().top);
                })()
            """,
            "returnByValue": True
        })
        print(f"   {r.get('result',{}).get('value','')}")

        # 8. Esperar publicacion
        print("[8] Esperando 15s para confirmacion...")
        await keepalive(c, 15)
        await screenshot(c, "tiktok_recover_3_posted.png")

        url_r = await c.send("Runtime.evaluate", {"expression":"window.location.href","returnByValue":True})
        title_r = await c.send("Runtime.evaluate", {"expression":"document.title","returnByValue":True})
        print(f"\n[FINAL URL] {url_r.get('result',{}).get('value','')}")
        print(f"[FINAL TITLE] {title_r.get('result',{}).get('value','')}")


asyncio.run(main())
