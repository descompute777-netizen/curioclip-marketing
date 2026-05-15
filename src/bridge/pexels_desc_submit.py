"""
Llena la descripción faltante en Pexels y genera la API key.
python -m src.bridge.pexels_desc_submit
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]
DESCRIPTION = "CurioClip uses Pexels CC0 videos as B-roll for a Spanish-language educational social media channel on TikTok. We use the videos in compliance with the Pexels license for original video content creation."

def _id(): _ID[0] += 1; return _ID[0]

def get_ws():
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "pexels.com" in t.get("url", ""):
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
            return ws
    return None

def cdp(ws, m, p=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid: return r
        except: return None

def click(ws, x, y):
    for t in ["mousePressed", "mouseReleased"]:
        cdp(ws, "Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})
    time.sleep(0.4)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

FILL_DESC_JS = f"""
(function() {{
    var ta = document.querySelector("textarea");
    if (!ta) return "no textarea";
    ta.focus();
    var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
    if (setter) {{
        setter.call(ta, {json.dumps(DESCRIPTION)});
    }} else {{
        ta.value = {json.dumps(DESCRIPTION)};
    }}
    ta.dispatchEvent(new Event("input", {{bubbles: true}}));
    ta.dispatchEvent(new Event("change", {{bubbles: true}}));
    return "ok:" + ta.value.length;
}})()
"""

CHECK_BTN_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button"));
    var btn = btns.find(function(b) { return b.textContent.trim().includes("Generate"); });
    if (btn) {
        var r = btn.getBoundingClientRect();
        return JSON.stringify({
            text: btn.textContent.trim(),
            disabled: btn.disabled,
            x: Math.round(r.left + r.width/2),
            y: Math.round(r.top + r.height/2)
        });
    }
    return null;
})()
"""

FIND_KEY_JS = """
(function() {
    var inputs = Array.from(document.querySelectorAll("input"));
    for (var i = 0; i < inputs.length; i++) {
        var v = (inputs[i].value || "").trim();
        if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return "INPUT:" + v;
    }
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    var node;
    while ((node = walker.nextNode())) {
        var t = node.textContent.trim();
        if (t.length >= 32 && t.length <= 64 && /^[A-Za-z0-9]+$/.test(t)) return "TEXT:" + t;
    }
    return null;
})()
"""


def main():
    print("=" * 50)
    print("PEXELS DESC + SUBMIT")
    print("=" * 50)

    ws = get_ws()
    if not ws:
        print("No Pexels tab found")
        return

    url = js(ws, "window.location.href")
    print(f"\nURL actual: {url}")

    # Llenar descripción
    print("\n[1] Llenando descripción...")
    desc_result = js(ws, FILL_DESC_JS)
    print(f"  {desc_result}")
    time.sleep(0.5)

    # Verificar botón
    print("\n[2] Estado del botón Generate...")
    btn_raw = js(ws, CHECK_BTN_JS)
    print(f"  {btn_raw}")
    ss(ws, "pex_ready.png")

    if btn_raw:
        btn = json.loads(btn_raw)
        if not btn.get("disabled"):
            print(f"\n[3] Click Generate API Key en ({btn['x']},{btn['y']})...")
            click(ws, btn['x'], btn['y'])
            time.sleep(10)
            ss(ws, "pex_generated.png")

            url = js(ws, "window.location.href")
            print(f"  URL: {url}")
            page = js(ws, "document.body.innerText") or ""
            print(f"  Texto: {page[:500]}")

            key_raw = js(ws, FIND_KEY_JS)
            if key_raw and (key_raw.startswith("INPUT:") or key_raw.startswith("TEXT:")):
                key = key_raw.split(":", 1)[1]
                print(f"\n✅ PEXELS API KEY: {key}")
                content = ENV.read_text(encoding="utf-8")
                if "PEXELS_API_KEY" in content:
                    content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
                else:
                    content += f"\nPEXELS_API_KEY={key}\n"
                ENV.write_text(content, encoding="utf-8")
                print("  ✅ Guardada en .env")
            else:
                print(f"\n  Key no encontrada. Ver pex_generated.png")
        else:
            print(f"  Botón aún disabled. Campos que faltan:")
            page = js(ws, "document.body.innerText") or ""
            print(f"  {page[:400]}")
            ss(ws, "pex_still_disabled.png")
    else:
        print("  Botón Generate no encontrado")

    ws.close()


if __name__ == "__main__":
    main()
