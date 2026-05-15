"""Trigger redeploy desde la página del deployment fallido."""
import asyncio, json, urllib.request, urllib.parse, base64, time
import websockets


DEPLOY_URL = "https://vercel.com/descompute777-2475s-projects/curioclip-marketing/9mJa8648WwD611qbKdCRPucywvJL"


async def main():
    cb = str(int(time.time()))
    url = f"{DEPLOY_URL}?_={cb}"
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
                    print(f"[shot] {name}"); return
                await asyncio.sleep(2)
        async def click_xy(x, y):
            for px, py in [(x-30,y-20),(x-10,y-5),(x,y)]:
                await call("Input.dispatchMouseEvent", {"type":"mouseMoved","x":px,"y":py})
                await asyncio.sleep(0.15)
            await call("Input.dispatchMouseEvent",
                       {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
            await call("Input.dispatchMouseEvent",
                       {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})

        await call("Page.enable"); await call("Runtime.enable")
        await call("Target.activateTarget", {"targetId": tab["id"]})
        await asyncio.sleep(10)

        print(f"[URL] {await js('window.location.href')}")
        await shot("redeploy_01.png")

        # Buscar botón Redeploy directo (puede aparecer cuando el deploy falló) o el menú ⋯
        find_r = await js(r"""
            (() => {
                // Candidato 1: botón Redeploy visible directo
                const btns = Array.from(document.querySelectorAll('button'));
                const re = btns.find(b => /^Redeploy$/i.test((b.textContent||'').trim()) && b.offsetParent !== null && !b.disabled);
                if (re) {
                    re.scrollIntoView({block:'center'});
                    const r = re.getBoundingClientRect();
                    return JSON.stringify({state:'direct', x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                }
                // Candidato 2: menú ⋯ (aria-label contains 'More' o button con SVG sin texto)
                const moreBtns = btns.filter(b => {
                    const lbl = (b.getAttribute('aria-label') || '').toLowerCase();
                    const txt = (b.textContent || '').trim();
                    return b.offsetParent !== null && !b.disabled && (lbl.includes('more') || lbl.includes('options') || lbl.includes('actions') || txt === '...' || txt === '');
                });
                return JSON.stringify({
                    state: 'no_direct',
                    moreCandidates: moreBtns.slice(0, 5).map(b => ({
                        lbl: b.getAttribute('aria-label') || '',
                        txt: (b.textContent||'').trim().slice(0, 30),
                        x: Math.round(b.getBoundingClientRect().x + b.getBoundingClientRect().width/2),
                        y: Math.round(b.getBoundingClientRect().y + b.getBoundingClientRect().height/2)
                    }))
                });
            })()
        """)
        rd = json.loads(find_r)
        print(f"[REDEPLOY-FIND] {rd}")

        if rd.get("state") == "direct":
            await click_xy(rd["x"], rd["y"])
            print(f"[CLICK] Redeploy direct @ ({rd['x']},{rd['y']})")
            await asyncio.sleep(4)
            await shot("redeploy_02_modal.png")
        else:
            # Probar el primer "more" candidato
            cands = rd.get("moreCandidates", [])
            if cands:
                c = cands[0]
                await click_xy(c["x"], c["y"])
                print(f"[CLICK] More @ ({c['x']},{c['y']})")
                await asyncio.sleep(2)
                await shot("redeploy_02_menu.png")
                # Buscar Redeploy en menú abierto
                menu_r = await js(r"""
                    (() => {
                        const items = Array.from(document.querySelectorAll('[role="menuitem"], button, a'))
                            .filter(el => /^Redeploy/i.test((el.textContent||'').trim()) && el.offsetParent !== null);
                        if (!items.length) return JSON.stringify({state:'no_menu_item'});
                        const it = items[0];
                        const r = it.getBoundingClientRect();
                        return JSON.stringify({state:'ready', x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                    })()
                """)
                mn = json.loads(menu_r)
                print(f"[MENU] {mn}")
                if mn.get("state") == "ready":
                    await click_xy(mn["x"], mn["y"])
                    print(f"[CLICK] Redeploy menu @ ({mn['x']},{mn['y']})")
                    await asyncio.sleep(4)
                    await shot("redeploy_03_modal.png")

        # Confirmación del modal: clic en el Redeploy del modal
        for attempt in range(5):
            confirm_r = await js(r"""
                (() => {
                    // En el modal el botón confirma es típicamente "Redeploy" en un dialog
                    const dialog = document.querySelector('[role="dialog"], [aria-modal="true"]');
                    if (dialog) {
                        const btn = Array.from(dialog.querySelectorAll('button'))
                            .find(b => /^Redeploy$/i.test((b.textContent||'').trim()) && !b.disabled);
                        if (btn) {
                            const r = btn.getBoundingClientRect();
                            return JSON.stringify({state:'ready_in_dialog', x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                        }
                    }
                    // Fallback: buscar botón Redeploy global
                    const btns = Array.from(document.querySelectorAll('button'))
                        .filter(b => /^Redeploy$/i.test((b.textContent||'').trim()) && b.offsetParent !== null && !b.disabled);
                    if (btns.length) {
                        const b = btns[btns.length - 1];
                        const r = b.getBoundingClientRect();
                        return JSON.stringify({state:'ready_fallback', x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                    }
                    return JSON.stringify({state:'no_confirm'});
                })()
            """)
            cm = json.loads(confirm_r)
            print(f"  [confirm-check {attempt+1}] {cm}")
            if cm.get("state", "").startswith("ready"):
                await click_xy(cm["x"], cm["y"])
                print(f"[CLICK] Confirm Redeploy @ ({cm['x']},{cm['y']})")
                await asyncio.sleep(5)
                break
            await asyncio.sleep(2)

        await shot("redeploy_04_after.png")

        # Monitor URL para ver redirect al nuevo deployment
        for i in range(30):
            await asyncio.sleep(4)
            cur = await js("window.location.href")
            print(f"  [+{(i+1)*4}s] {cur[:160]}")
            if "/9mJa8648" not in cur and "/dpl_" in cur:
                print("[NEW DEPLOYMENT URL DETECTADA]")
                break
            if "deploymentIds=dpl_" in cur:
                print("[NEW DEPLOY OK]")
                break

        await shot("redeploy_05_final.png")
        # Capturar links de producción si existen
        links = await js(r"""
            (() => {
                const ls = Array.from(document.querySelectorAll('a'))
                    .map(a => a.href || '')
                    .filter(h => h.includes('.vercel.app'));
                return JSON.stringify([...new Set(ls)].slice(0, 15));
            })()
        """)
        print(f"[PROD LINKS] {links}")


asyncio.run(main())
