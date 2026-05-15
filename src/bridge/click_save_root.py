"""Click Save exacto del card Root Directory."""
import asyncio, json, urllib.request, base64, time
import websockets


async def main():
    with urllib.request.urlopen("http://localhost:9222/json", timeout=5) as r:
        tabs = json.loads(r.read())
    tab = next((t for t in tabs if t.get("type") == "page"
                and "settings/build-and-deployment" in t.get("url", "")), None)
    if not tab:
        print("[FAIL] no settings tab"); return
    print(f"[OK] Tab: {tab['url'][:120]}")

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

        await call("Page.enable"); await call("Runtime.enable")
        await call("Target.activateTarget", {"targetId": tab["id"]})
        await asyncio.sleep(2)

        # Verificar valor actual y re-setear si hizo falta
        val_r = await js(r"""
            (() => {
                const ins = Array.from(document.querySelectorAll('input'))
                    .filter(i => i.offsetParent !== null && !i.disabled);
                const target = ins.find(i => i.value === 'web' || i.value === './' || i.value === '');
                if (!target) return JSON.stringify({state:'no_input'});
                if (target.value !== 'web') {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(target, 'web');
                    target.dispatchEvent(new Event('input', {bubbles: true}));
                    target.dispatchEvent(new Event('change', {bubbles: true}));
                }
                return JSON.stringify({state:'ok', val: target.value});
            })()
        """)
        print(f"[VAL] {val_r}")
        await asyncio.sleep(1.5)

        # Encontrar EXACTAMENTE el botón Save de la sección Root Directory
        # Esta sección es identificable porque contiene el header "Root Directory"
        find_save = await js(r"""
            (() => {
                // Buscar el ANCESTRO común (la card/section) que contenga el header "Root Directory"
                const header = Array.from(document.querySelectorAll('h2, h3, h4, label, div, span, p'))
                    .find(el => (el.textContent||'').trim() === 'Root Directory' && el.offsetParent !== null);
                if (!header) return JSON.stringify({state:'no_header'});
                // Subir hasta encontrar un section/article/div grande que contenga un botón Save
                let p = header;
                for (let i = 0; i < 12 && p; i++) {
                    const saves = Array.from(p.querySelectorAll('button')).filter(b =>
                        /^Save$/i.test((b.textContent||'').trim()) && b.offsetParent !== null
                    );
                    if (saves.length === 1) {
                        const s = saves[0];
                        s.scrollIntoView({block:'center'});
                        const r = s.getBoundingClientRect();
                        return JSON.stringify({
                            state:'ready', depth: i, disabled: s.disabled,
                            x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)
                        });
                    }
                    if (saves.length > 1) {
                        // demasiados — seguir subiendo no ayudará; tomar el primero del card actual
                        const s = saves[0];
                        const r = s.getBoundingClientRect();
                        return JSON.stringify({
                            state:'multi', count: saves.length,
                            x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)
                        });
                    }
                    p = p.parentElement;
                }
                return JSON.stringify({state:'no_save_in_section'});
            })()
        """)
        sv = json.loads(find_save)
        print(f"[SAVE] {sv}")
        if sv.get("state") not in ("ready", "multi"):
            return
        x, y = sv["x"], sv["y"]
        await asyncio.sleep(0.5)
        for px, py in [(x-30,y-20),(x-10,y-5),(x,y)]:
            await call("Input.dispatchMouseEvent", {"type":"mouseMoved","x":px,"y":py})
            await asyncio.sleep(0.15)
        await call("Input.dispatchMouseEvent",
                   {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
        await call("Input.dispatchMouseEvent",
                   {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})
        print(f"[CLICK] Save @ ({x},{y})")
        await asyncio.sleep(6)
        await shot("save_root_after.png")

        # Verificar que el input siga con 'web' y que Save quedó disabled (confirmación)
        post = await js(r"""
            (() => {
                const ins = Array.from(document.querySelectorAll('input'))
                    .filter(i => i.offsetParent !== null && !i.disabled);
                const target = ins.find(i => i.value === 'web' || i.value === './' || i.value === '');
                const saves = Array.from(document.querySelectorAll('button'))
                    .filter(b => /^Save$/i.test((b.textContent||'').trim()));
                return JSON.stringify({
                    inputVal: target ? target.value : 'no_input',
                    savesDisabled: saves.map(b => b.disabled),
                    toast: (document.body.innerText || '').slice(0, 600)
                });
            })()
        """)
        print(f"[POST] {post[:800]}")


asyncio.run(main())
