"""Leer el log completo del build fallido desde la página activa."""
import asyncio, json, urllib.request, time
import websockets


async def main():
    # Buscar la tab activa con el deployment
    with urllib.request.urlopen("http://localhost:9222/json", timeout=5) as r:
        tabs = json.loads(r.read())
    tab = next((t for t in tabs if t.get("type") == "page" and "vercel.com/new/import" in t.get("url", "") and "deploymentIds" in t.get("url", "")), None)
    if not tab:
        # Fallback: cualquier tab vercel
        tab = next((t for t in tabs if t.get("type") == "page" and "vercel.com" in t.get("url", "")), None)
    if not tab:
        print("[FAIL] no Vercel tab"); return
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
                    return d.get("result", {})
        async def js(expr):
            r = await call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
            return r.get("result", {}).get("value", "")

        await call("Runtime.enable")
        await call("Target.activateTarget", {"targetId": tab["id"]})
        await asyncio.sleep(2)

        # Scroll al área de Build Logs y expandir Deployment Summary
        await js("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)

        # Click en Deployment Summary para expandirlo
        await js(r"""
            (() => {
                const headers = Array.from(document.querySelectorAll('*'))
                    .filter(el => (el.textContent || '').trim() === 'Deployment Summary' && el.offsetParent !== null);
                if (headers.length) {
                    const h = headers[0];
                    let p = h;
                    for (let i=0; i<4 && p; i++) {
                        if (p.tagName === 'BUTTON' || p.getAttribute('role') === 'button' || p.onclick) {
                            p.click(); return 'clicked';
                        }
                        p = p.parentElement;
                    }
                    h.click();
                    return 'clicked-direct';
                }
                return 'no-header';
            })()
        """)
        await asyncio.sleep(2)

        # Volcado de todo texto relevante: build logs, error summary
        full_dump = await js(r"""
            (() => {
                // Buscar elementos que tengan timestamps tipo "16:14:50"
                const allText = document.body.innerText;
                // Cortar después de "Build Logs"
                const idx = allText.indexOf('Build Logs');
                const tail = idx >= 0 ? allText.slice(idx, idx + 8000) : allText.slice(0, 8000);
                return tail;
            })()
        """)
        with open("build_log.txt", "w", encoding="utf-8") as f:
            f.write(full_dump)
        print(f"[saved] build_log.txt ({len(full_dump)} chars)")


asyncio.run(main())
