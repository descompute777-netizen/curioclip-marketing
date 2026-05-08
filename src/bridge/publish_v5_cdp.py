"""Publica V5 en TikTok usando CDP raw — sin Playwright."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, asyncio, urllib.request, urllib.parse, base64
from pathlib import Path
import websockets

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
VIDEO = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_01_2026-05-06_a_2026-05-12" / "VIERNES" / "OUTPUT" / "V5_final.mp4"


async def cdp_send(ws, method, params=None, msg_id_ref=[0]):
    msg_id_ref[0] += 1
    mid = msg_id_ref[0]
    await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        data = json.loads(await ws.recv())
        if data.get("id") == mid:
            if "error" in data:
                print(f"[CDP ERR] {method}: {data['error']}")
            return data.get("result", {})


async def main():
    print(f"[OK] Video: {VIDEO} ({VIDEO.stat().st_size//1024} KB)")

    # 1. Crear tab para el upload
    upload_url = "https://www.tiktok.com/tiktokstudio/upload?from=upload"
    req = urllib.request.Request(
        f"http://localhost:9222/json/new?{urllib.parse.quote(upload_url)}",
        method="PUT"
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        tab = json.loads(r.read())
    print(f"[CDP] Tab: {tab['id'][:16]}...")
    ws_url = tab["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url, max_size=64*1024*1024) as ws:
        msg_id_ref = [0]
        async def send(m, p=None): return await cdp_send(ws, m, p, msg_id_ref)

        await send("Page.enable")
        await send("DOM.enable")
        await send("Runtime.enable")
        await send("Target.activateTarget", {"targetId": tab["id"]})

        # 2. Esperar a que la pagina cargue
        print("[CDP] Esperando 25s para que la pagina renderice...")
        await asyncio.sleep(25)

        # 3. Buscar el file input via Runtime.evaluate
        print("[CDP] Buscando input[type=file]...")
        result = await send("Runtime.evaluate", {
            "expression": """
                (() => {
                    const inputs = document.querySelectorAll('input[type="file"]');
                    return Array.from(inputs).map((el, i) => ({
                        index: i,
                        accept: el.accept || '',
                        visible: el.offsetParent !== null
                    }));
                })()
            """,
            "returnByValue": True
        })
        inputs = result.get("result", {}).get("value", [])
        print(f"[CDP] Inputs encontrados: {len(inputs)}")
        for i, inp in enumerate(inputs):
            print(f"  [{i}] accept={inp['accept']!r} visible={inp['visible']}")

        if not inputs:
            print("[FAIL] No file inputs found. La pagina puede no haber cargado.")
            await send("Page.captureScreenshot", {"format": "png"})
            return

        # 4. Buscar el primer input que acepta video
        target_idx = 0
        for i, inp in enumerate(inputs):
            if "video" in inp["accept"]:
                target_idx = i
                break

        # 5. Get nodeId del input
        doc_result = await send("DOM.getDocument")
        root_id = doc_result["root"]["nodeId"]
        node_result = await send("DOM.querySelectorAll", {
            "nodeId": root_id,
            "selector": "input[type='file']"
        })
        node_ids = node_result["nodeIds"]
        if not node_ids:
            print("[FAIL] No se obtuvieron nodeIds")
            return
        target_node = node_ids[target_idx] if target_idx < len(node_ids) else node_ids[0]
        print(f"[CDP] Target nodeId: {target_node}")

        # 6. setFileInputFiles
        await send("DOM.setFileInputFiles", {
            "files": [str(VIDEO)],
            "nodeId": target_node
        })
        print(f"[OK] Archivo seteado: {VIDEO.name}")

        # 7. Esperar procesamiento
        print("[CDP] Esperando 30s para procesamiento del video...")
        await asyncio.sleep(30)

        # 8. Screenshot del estado
        result = await send("Page.captureScreenshot", {"format": "png"})
        if "data" in result:
            with open("tiktok_upload_complete.png", "wb") as f:
                f.write(base64.b64decode(result["data"]))
            print("[OK] Screenshot: tiktok_upload_complete.png")

        print()
        print("===> Ahora ve a tu Chrome, ajusta caption si quieres y dale POSTEAR.")


asyncio.run(main())
