"""Cambiar Root Directory './' → 'web' y guardar (input es editable directo, sin Edit btn)."""
import asyncio, json, urllib.request, urllib.parse, base64, time
import websockets


BD_URL = "https://vercel.com/descompute777-2475s-projects/curioclip-marketing/settings/build-and-deployment"


async def main():
    cb = str(int(time.time()))
    url = f"{BD_URL}?_={cb}"
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

        await call("Page.enable"); await call("Runtime.enable")
        await call("Target.activateTarget", {"targetId": tab["id"]})
        await asyncio.sleep(10)

        # Scroll a Root Directory
        await js(r"""
            (() => {
                const h = Array.from(document.querySelectorAll('*'))
                    .find(el => (el.textContent||'').trim() === 'Root Directory' && el.offsetParent !== null);
                if (h) h.scrollIntoView({block:'center'});
            })()
        """)
        await asyncio.sleep(2)
        await shot("fix_a_scroll.png")

        # Setear el value vía React-friendly approach
        set_r = await js(r"""
            (() => {
                // Encontrar el input cuyo valor es './' o que está dentro del card Root Directory
                const ins = Array.from(document.querySelectorAll('input'))
                    .filter(i => i.offsetParent !== null && !i.disabled && !i.readOnly && (i.type === 'text' || !i.type || i.type === ''));
                // Preferir el que tenga value './' o que esté cerca del header Root Directory
                let target = ins.find(i => (i.value || '').trim() === './' || (i.value || '').trim() === '');
                if (!target) {
                    const lbl = Array.from(document.querySelectorAll('*'))
                        .find(el => (el.textContent||'').trim() === 'Root Directory' && el.offsetParent !== null);
                    if (lbl) {
                        const lr = lbl.getBoundingClientRect();
                        target = ins.reduce((best, i) => {
                            const br = i.getBoundingClientRect();
                            if (br.y < lr.y) return best;
                            const d = Math.abs(br.y - lr.y);
                            if (!best || d < best.d) return {i, d};
                            return best;
                        }, null);
                        target = target ? target.i : null;
                    }
                }
                if (!target) return JSON.stringify({state:'no_input'});

                // Disparar evento React: usar nativeInputValueSetter
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                target.focus();
                setter.call(target, 'web');
                target.dispatchEvent(new Event('input', {bubbles: true}));
                target.dispatchEvent(new Event('change', {bubbles: true}));
                const r = target.getBoundingClientRect();
                return JSON.stringify({state:'ok', val_now: target.value, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
            })()
        """)
        print(f"[SET] {set_r}")
        await asyncio.sleep(2)
        await shot("fix_b_typed.png")

        # Buscar el Save asociado al card de Root Directory (el más cercano abajo)
        save_r = await js(r"""
            (() => {
                const lbl = Array.from(document.querySelectorAll('*'))
                    .find(el => (el.textContent||'').trim() === 'Root Directory' && el.offsetParent !== null);
                if (!lbl) return JSON.stringify({state:'no_label'});
                const lr = lbl.getBoundingClientRect();
                // Buscar todos los Save visibles y NO disabled
                const saves = Array.from(document.querySelectorAll('button'))
                    .filter(b => /^Save$/i.test((b.textContent||'').trim()) && b.offsetParent !== null && !b.disabled);
                if (!saves.length) {
                    // También listar todos los Save aunque estén disabled
                    const allSaves = Array.from(document.querySelectorAll('button'))
                        .filter(b => /^Save$/i.test((b.textContent||'').trim()))
                        .map(b => ({v: b.offsetParent !== null, d: b.disabled, y: Math.round(b.getBoundingClientRect().y)}));
                    return JSON.stringify({state:'no_enabled_save', all: allSaves});
                }
                // Tomar el Save cuya posición Y esté justo después de Root Directory
                let best = null;
                for (const s of saves) {
                    const r = s.getBoundingClientRect();
                    if (r.y < lr.y) continue;
                    const d = r.y - lr.y;
                    if (!best || d < best.d) best = {s, d, r};
                }
                if (!best) return JSON.stringify({state:'no_below_save'});
                best.s.scrollIntoView({block:'center'});
                return JSON.stringify({state:'ready', x: Math.round(best.r.x + best.r.width/2), y: Math.round(best.r.y + best.r.height/2)});
            })()
        """)
        sv = json.loads(save_r)
        print(f"[SAVE] {sv}")
        if sv.get("state") == "ready":
            x, y = sv["x"], sv["y"]
            for px, py in [(x-30,y-20),(x-10,y-5),(x,y)]:
                await call("Input.dispatchMouseEvent", {"type":"mouseMoved","x":px,"y":py})
                await asyncio.sleep(0.2)
            await call("Input.dispatchMouseEvent",
                       {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1})
            await call("Input.dispatchMouseEvent",
                       {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1})
            print("[CLICK] Save")
            await asyncio.sleep(6)
            await shot("fix_c_saved.png")
            print(f"[URL] {await js('window.location.href')}")
            # Check toast / confirmación
            toast = await js(r"""
                (() => {
                    const t = (document.body.innerText || '').slice(0, 2000);
                    const hasSaved = /saved|updated|success/i.test(t);
                    return JSON.stringify({hasSaved, snippet: t.slice(0, 500)});
                })()
            """)
            print(f"[POSTSAVE] {toast[:600]}")


asyncio.run(main())
