"""Raw CDP screenshot — sin Playwright, sin hangs."""
import json, sys, base64, urllib.request, asyncio, websockets, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--url", required=True, help="URL local file:// o https://")
ap.add_argument("--out", required=True)
ap.add_argument("--wait", type=int, default=12)
args = ap.parse_args()


async def main():
    # 1. Crear nueva pestana via HTTP
    print(f"[CDP] Creando nueva tab para {args.url}")
    req = urllib.request.Request(
        f"http://localhost:9222/json/new?{urllib.parse.quote(args.url)}",
        method="PUT"
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        tab = json.loads(r.read())
    print(f"[CDP] Tab id: {tab['id'][:16]}...")
    ws_url = tab["webSocketDebuggerUrl"]

    # 2. Conectar al WS de la tab
    async with websockets.connect(ws_url, max_size=64*1024*1024) as ws:
        msg_id = 0
        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
            while True:
                data = json.loads(await ws.recv())
                if data.get("id") == msg_id:
                    return data

        await send("Page.enable")
        await send("Page.navigate", {"url": args.url})
        # esperar render
        print(f"[CDP] Esperando {args.wait}s para render...")
        await asyncio.sleep(args.wait)
        # screenshot
        print("[CDP] Capturando screenshot...")
        result = await send("Page.captureScreenshot", {"format": "png"})
        b64 = result["result"]["data"]
        with open(args.out, "wb") as f:
            f.write(base64.b64decode(b64))
        print(f"[OK] {args.out}")

import urllib.parse
asyncio.run(main())
