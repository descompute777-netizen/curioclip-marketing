"""Diagnóstico: buscar el elemento Import en vercel.com/new."""
import asyncio, json, urllib.request, urllib.parse, time
import websockets


async def main():
    cb = str(int(time.time()))
    url = f"https://vercel.com/new?_={cb}"
    req = urllib.request.Request(
        f"http://localhost:9222/json/new?{urllib.parse.quote(url)}", method="PUT"
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        tab = json.loads(r.read())

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

        await call("Page.enable"); await call("Runtime.enable")
        await call("Target.activateTarget", {"targetId": tab["id"]})
        await asyncio.sleep(10)

        # Dump TODO elemento con texto "Import" exacto, visible
        dump = await js(r"""
            (() => {
                const all = Array.from(document.querySelectorAll('*'));
                const matches = [];
                for (const el of all) {
                    const own = Array.from(el.childNodes)
                        .filter(n => n.nodeType === 3)
                        .map(n => n.textContent.trim()).join('').trim();
                    if (own === 'Import' && el.offsetParent !== null) {
                        const r = el.getBoundingClientRect();
                        matches.push({
                            tag: el.tagName,
                            cls: (el.className || '').toString().slice(0, 80),
                            role: el.getAttribute('role') || '',
                            href: el.href || el.getAttribute('href') || '',
                            x: Math.round(r.x + r.width/2),
                            y: Math.round(r.y + r.height/2),
                            w: Math.round(r.width),
                            h: Math.round(r.height)
                        });
                    }
                }
                return JSON.stringify(matches.slice(0, 10));
            })()
        """)
        print(f"[IMPORT-MATCHES] {dump}")

        # Buscar links a /import o /new que contengan curioclip
        links = await js(r"""
            (() => {
                const ls = Array.from(document.querySelectorAll('a'))
                    .filter(a => a.offsetParent !== null)
                    .map(a => ({href: a.href || '', text: (a.textContent || '').trim().slice(0,80)}))
                    .filter(o => o.href.includes('curioclip') || o.href.includes('/import') || /Import/i.test(o.text));
                return JSON.stringify(ls.slice(0, 15));
            })()
        """)
        print(f"[LINKS] {links}")


asyncio.run(main())
