"""Tras OAuth, refrescar Vercel /new y verificar acceso al repo."""
import asyncio, json, urllib.request, urllib.parse, base64, time
import websockets


async def main():
    # Crear tab nueva con cache buster
    cb = str(int(time.time()))
    url = f"https://vercel.com/new?_={cb}"
    req = urllib.request.Request(f"http://localhost:9222/json/new?{urllib.parse.quote(url)}", method="PUT")
    with urllib.request.urlopen(req, timeout=8) as r:
        tab = json.loads(r.read())
    print(f"[OK] Fresh tab: {tab['id'][:16]}")

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
        await asyncio.sleep(8)

        sc = await s("Page.captureScreenshot", {"format": "png"})
        with open("after_oauth_state.png", "wb") as f: f.write(base64.b64decode(sc["data"]))
        print("[shot] after_oauth_state.png")

        # Type the repo URL
        coords_r = await s("Runtime.evaluate", {
            "expression": r"""
                (() => {
                    const ins = Array.from(document.querySelectorAll('input, textarea')).find(el => {
                        const ph = (el.placeholder || '').toLowerCase();
                        return (ph.includes('git') || ph.includes('v0')) && el.offsetParent !== null;
                    });
                    if (!ins) return null;
                    ins.focus();
                    const r = ins.getBoundingClientRect();
                    return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)});
                })()
            """,
            "returnByValue": True
        })
        coords = json.loads(coords_r.get('result',{}).get('value','{}'))
        await s("Input.dispatchMouseEvent", {"type":"mousePressed","x":coords['x'],"y":coords['y'],"button":"left","clickCount":1})
        await s("Input.dispatchMouseEvent", {"type":"mouseReleased","x":coords['x'],"y":coords['y'],"button":"left","clickCount":1})
        await asyncio.sleep(0.5)
        await s("Input.insertText", {"text": "https://github.com/descompute777-netizen/curioclip-marketing"})
        await asyncio.sleep(3)

        sc = await s("Page.captureScreenshot", {"format": "png"})
        with open("after_oauth_typed.png", "wb") as f: f.write(base64.b64decode(sc["data"]))
        print("[shot] after_oauth_typed.png")

        # Verificar mensaje de "Could not access" o si Deploy esta habilitado
        check = await s("Runtime.evaluate", {
            "expression": r"""
                (() => {
                    const errMsg = document.body.textContent.includes('Could not access');
                    const deployBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Deploy');
                    return JSON.stringify({
                        error: errMsg,
                        deploy_disabled: deployBtn ? deployBtn.disabled : 'no_btn'
                    });
                })()
            """,
            "returnByValue": True
        })
        print(f"[STATE] {check.get('result',{}).get('value','')}")

        # Click Deploy si todo OK
        await asyncio.sleep(1)
        click_r = await s("Runtime.evaluate", {
            "expression": r"""
                (() => {
                    const b = Array.from(document.querySelectorAll('button')).find(x => x.textContent.trim() === 'Deploy' && !x.disabled && x.offsetParent !== null);
                    if (b) { b.click(); return 'deploy_clicked'; }
                    return 'deploy_blocked_or_missing';
                })()
            """,
            "returnByValue": True
        })
        print(f"[CLICK] {click_r.get('result',{}).get('value','')}")

        # Monitor URL
        for i in range(20):
            await asyncio.sleep(4)
            url_r = await s("Runtime.evaluate", {"expression":"window.location.href","returnByValue":True})
            url = url_r.get('result',{}).get('value','')
            print(f"  [+{(i+1)*4}s] {url[:140]}")
            if "vercel.com/" in url and url != f"https://vercel.com/new?_={cb}" and "/new" not in url:
                print("[DEPLOY DETECTED]")
                break
            if "/import" in url or "/dep_" in url or "deployments" in url:
                break

        sc = await s("Page.captureScreenshot", {"format": "png"})
        with open("after_oauth_deploy.png", "wb") as f: f.write(base64.b64decode(sc["data"]))


asyncio.run(main())
