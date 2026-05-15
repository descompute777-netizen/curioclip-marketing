"""Activar tab Authorize Vercel + Click Authorize."""
import asyncio, json, urllib.request, base64
import websockets


async def main():
    with urllib.request.urlopen("http://localhost:9222/json", timeout=5) as r:
        tabs = json.loads(r.read())
    tab = next((t for t in tabs if t.get("type")=="page" and "github.com/login/oauth/authorize" in t.get("url","")), None)
    if not tab:
        print("[FAIL] no Authorize tab"); return
    print(f"[OK] Tab: {tab['title'][:40]}")

    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=64*1024*1024,
                                   ping_interval=5, ping_timeout=60) as ws:
        mid = 0
        async def s(m, p=None):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
            while True:
                d = json.loads(await ws.recv())
                if d.get("id") == mid: return d.get("result", {})

        await s("Page.enable"); await s("Runtime.enable")
        await s("Target.activateTarget", {"targetId": tab["id"]})
        await asyncio.sleep(2)

        # Screenshot first to see what's there
        sc = await s("Page.captureScreenshot", {"format": "png"})
        with open("authorize_before.png", "wb") as f: f.write(base64.b64decode(sc["data"]))
        print("[shot] authorize_before.png")

        # Scroll all the way down primero
        await s("Runtime.evaluate", {"expression": "window.scrollTo(0, document.body.scrollHeight)", "returnByValue": True})
        await asyncio.sleep(2)

        # GitHub anti-clickjacking: necesita mouse movement antes de que el boton se habilite
        # Simulamos mouse movement orgánico
        print("[MOUSE] Simulando movimiento del cursor para desbloquear...")
        for px, py in [(100,100), (200,200), (300,300), (394,300), (394,364)]:
            await s("Input.dispatchMouseEvent", {"type":"mouseMoved","x":px,"y":py})
            await asyncio.sleep(0.4)

        # Esperar que el boton se habilite (GitHub a veces lo bloquea unos segundos)
        for attempt in range(8):
            r = await s("Runtime.evaluate", {
                "expression": r"""
                    (() => {
                        const btns = Array.from(document.querySelectorAll('button, input[type="submit"]'));
                        const auth = btns.find(b => {
                            const t = (b.textContent || b.value || '').trim();
                            return /^Authorize/i.test(t);
                        });
                        if (!auth) return JSON.stringify({err:'not_found'});
                        auth.scrollIntoView({block:'center'});
                        const r = auth.getBoundingClientRect();
                        return JSON.stringify({
                            text: (auth.textContent || auth.value || '').trim(),
                            disabled: auth.disabled,
                            ariaDisabled: auth.getAttribute('aria-disabled'),
                            x: Math.round(r.x + r.width/2),
                            y: Math.round(r.y + r.height/2)
                        });
                    })()
                """,
                "returnByValue": True
            })
            result_str = r.get('result',{}).get('value','')
            data = json.loads(result_str)
            print(f"  [attempt {attempt+1}] {data}")
            if 'err' in data:
                print("[FAIL] btn no existe"); return
            if not data.get('disabled') and data.get('ariaDisabled') != 'true':
                break
            print("    [WAIT] btn disabled, esperando 3s...")
            await asyncio.sleep(3)

        # Click via mouse
        await s("Input.dispatchMouseEvent", {"type":"mousePressed","x":data['x'],"y":data['y'],"button":"left","clickCount":1})
        await s("Input.dispatchMouseEvent", {"type":"mouseReleased","x":data['x'],"y":data['y'],"button":"left","clickCount":1})
        print(f"[CLICK] Authorize button at ({data['x']},{data['y']})")

        # Monitor URL para ver redirect
        for i in range(15):
            await asyncio.sleep(3)
            url_r = await s("Runtime.evaluate", {"expression":"window.location.href","returnByValue":True})
            url = url_r.get('result',{}).get('value','')
            print(f"  [+{(i+1)*3}s] {url[:140]}")
            if "vercel.com" in url:
                print("[REDIRECT a Vercel — OAuth aprobado]")
                break

        sc = await s("Page.captureScreenshot", {"format": "png"})
        with open("authorize_done.png", "wb") as f: f.write(base64.b64decode(sc["data"]))


asyncio.run(main())
