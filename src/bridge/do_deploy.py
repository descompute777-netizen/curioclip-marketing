"""Importar curioclip-marketing y hacer clic Deploy en Vercel.

URL directa de import (descubierta vía probe_import.py):
https://vercel.com/new/import?framework=python&id=1232847392&name=curioclip-marketing&owner=descompute777-netizen&provider=github&s=...

Esta URL salta directo al form configuración con framework Python autodetectado.
"""
import asyncio, json, urllib.request, urllib.parse, base64, time
import websockets


IMPORT_URL = (
    "https://vercel.com/new/import"
    "?framework=python"
    "&hasTrialAvailable=1"
    "&id=1232847392"
    "&name=curioclip-marketing"
    "&owner=descompute777-netizen"
    "&project-name=curioclip-marketing"
    "&provider=github"
    "&remainingProjects=1"
    "&s=https%3A%2F%2Fgithub.com%2Fdescompute777-netizen%2Fcurioclip-marketing"
    "&totalProjects=1"
)


async def main():
    cb = str(int(time.time()))
    url = f"{IMPORT_URL}&_={cb}"
    req = urllib.request.Request(
        f"http://localhost:9222/json/new?{urllib.parse.quote(url)}", method="PUT"
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        tab = json.loads(r.read())
    print(f"[OK] Tab: {tab['id'][:16]}")

    async with websockets.connect(
        tab["webSocketDebuggerUrl"], max_size=64 * 1024 * 1024,
        ping_interval=5, ping_timeout=60,
    ) as ws:
        mid = 0
        async def call(m, p=None):
            nonlocal mid
            mid += 1
            await ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
            while True:
                d = json.loads(await ws.recv())
                if d.get("id") == mid:
                    return d.get("result", {}), d.get("error")

        async def js(expr):
            r, _ = await call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
            return r.get("result", {}).get("value", "")

        async def shot(name):
            for _ in range(3):
                res, _ = await call("Page.captureScreenshot", {"format": "png"})
                if "data" in res:
                    with open(name, "wb") as f:
                        f.write(base64.b64decode(res["data"]))
                    print(f"[shot] {name}")
                    return
                await asyncio.sleep(2)

        async def click_xy(x, y):
            for px, py in [(x-40, y-30), (x-15, y-10), (x, y)]:
                await call("Input.dispatchMouseEvent", {"type":"mouseMoved","x":px,"y":py})
                await asyncio.sleep(0.2)
            await call("Input.dispatchMouseEvent",
                       {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
            await call("Input.dispatchMouseEvent",
                       {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})

        await call("Page.enable")
        await call("Runtime.enable")
        await call("Target.activateTarget", {"targetId": tab["id"]})
        await asyncio.sleep(12)

        print(f"[URL] {await js('window.location.href')}")
        await shot("do_deploy_01_config.png")

        # Scroll al fondo para asegurar visibilidad del Deploy
        await js("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        await shot("do_deploy_02_scrolled.png")

        # Esperar y clicar Deploy (puede ser button o link)
        deploy_clicked = False
        for attempt in range(25):
            deploy_r = await js(r"""
                (() => {
                    // Buscar elemento clickeable con texto exacto "Deploy"
                    const all = Array.from(document.querySelectorAll('*'));
                    const candidates = all.filter(el => {
                        const own = Array.from(el.childNodes)
                            .filter(n => n.nodeType === 3)
                            .map(n => n.textContent.trim()).join('').trim();
                        if (own !== 'Deploy' && (el.textContent||'').trim() !== 'Deploy') return false;
                        if (el.offsetParent === null) return false;
                        const tag = el.tagName;
                        return tag === 'BUTTON' || tag === 'A' || el.getAttribute('role') === 'button';
                    });
                    if (!candidates.length) {
                        // Probar buscando ancestros de <span>Deploy</span>
                        const spans = Array.from(document.querySelectorAll('span')).filter(s => {
                            return (s.textContent || '').trim() === 'Deploy' && s.offsetParent !== null;
                        });
                        for (const sp of spans) {
                            let p = sp;
                            for (let i=0; i<5 && p; i++) {
                                if (p.tagName === 'BUTTON' || p.tagName === 'A' || p.getAttribute && p.getAttribute('role') === 'button') {
                                    candidates.push(p); break;
                                }
                                p = p.parentElement;
                            }
                        }
                    }
                    const visible = candidates.filter(b => !b.disabled && b.getAttribute('aria-disabled') !== 'true');
                    if (!visible.length) {
                        const all_state = candidates.map(b => ({
                            tag: b.tagName, d: b.disabled,
                            aria: b.getAttribute('aria-disabled') || ''
                        }));
                        return JSON.stringify({state:'no_deploy', candidates: all_state.slice(0,5)});
                    }
                    const b = visible[visible.length - 1]; // último (el más cercano al fondo)
                    b.scrollIntoView({block:'center'});
                    const r = b.getBoundingClientRect();
                    return JSON.stringify({state:'ready', tag: b.tagName, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                })()
            """)
            ds = json.loads(deploy_r)
            print(f"  [check {attempt+1}] {ds}")
            if ds.get("state") == "ready":
                await asyncio.sleep(0.5)
                await click_xy(ds["x"], ds["y"])
                print(f"[CLICK] Deploy ({ds.get('tag')}) @ ({ds['x']},{ds['y']})")
                deploy_clicked = True
                break
            await asyncio.sleep(3)

        if not deploy_clicked:
            await shot("do_deploy_03_no_deploy.png")
            return

        # Monitor URL hasta ver redirect al dashboard del proyecto
        final_url = ""
        for i in range(60):
            await asyncio.sleep(3)
            cur = await js("window.location.href")
            print(f"  [+{(i+1)*3}s] {cur[:160]}")
            final_url = cur
            if "vercel.com" in cur and "/new" not in cur:
                if "curioclip" in cur.lower() or "/dashboard" in cur or "deployments" in cur:
                    print("[DEPLOY PROYECTO CREADO]")
                    break

        await shot("do_deploy_04_final.png")
        print(f"[FINAL_URL] {final_url}")

        prod_r = await js(r"""
            (() => {
                const links = Array.from(document.querySelectorAll('a'))
                    .map(a => a.href || '')
                    .filter(h => h.includes('.vercel.app') || h.includes('curioclip'));
                return JSON.stringify({links: [...new Set(links)].slice(0, 20)});
            })()
        """)
        print(f"[PROD LINKS] {prod_r}")


asyncio.run(main())
