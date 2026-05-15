"""
Tipea la descripción de Pexels con Input.insertText (React-compatible) y envía.
python -m src.bridge.pexels_type_submit
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]
DESC = "CurioClip uses Pexels CC0 videos as B-roll for Spanish-language educational content on TikTok and Facebook. Used per Pexels license for original video creation."

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
    time.sleep(0.3)

def key_ctrl_a(ws):
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})

def key_delete(ws):
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete", "code": "Delete"})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Delete", "code": "Delete"})

def insert_text(ws, text):
    # CDP insertText — eventos reales que React detecta
    cdp(ws, "Input.insertText", {"text": text})
    time.sleep(0.2)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

FIND_TEXTAREA_JS = """
(function() {
    var ta = document.querySelector("textarea");
    if (!ta) return null;
    var r = ta.getBoundingClientRect();
    return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
})()
"""

CHECK_BTN_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button"));
    var btn = btns.find(function(b) { return b.textContent.trim().includes("Generate"); });
    if (btn) {
        var r = btn.getBoundingClientRect();
        return JSON.stringify({text: btn.textContent.trim(), disabled: btn.disabled,
            x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
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
    print("PEXELS TYPE DESC + SUBMIT")
    print("=" * 50)

    ws = get_ws()
    if not ws:
        print("No Pexels tab"); return

    url = js(ws, "window.location.href")
    print(f"\nURL: {url}")

    # PASO 1: Localizar el textarea
    ta_raw = js(ws, FIND_TEXTAREA_JS)
    if not ta_raw:
        print("No textarea encontrado")
        return
    ta = json.loads(ta_raw)
    print(f"\n[1] Textarea en ({ta['x']}, {ta['y']})")

    # PASO 2: Click en el textarea para enfocarlo
    click(ws, ta['x'], ta['y'])
    time.sleep(0.3)

    # PASO 3: Seleccionar todo el contenido actual y borrarlo
    key_ctrl_a(ws)
    time.sleep(0.1)
    key_delete(ws)
    time.sleep(0.2)

    # PASO 4: Tipear la descripción usando insertText (React-compatible)
    print(f"\n[2] Tipeando descripción con insertText...")
    insert_text(ws, DESC)
    print(f"  Typed {len(DESC)} chars")
    time.sleep(0.5)

    # Verificar que React actualizó el estado
    ta_val = js(ws, "document.querySelector('textarea')?.value || 'not found'")
    print(f"  Textarea value: {str(ta_val)[:60]}")

    ss(ws, "type_ready.png")

    # PASO 5: Verificar estado del botón
    btn_raw = js(ws, CHECK_BTN_JS)
    print(f"\n[3] Botón: {btn_raw}")

    if btn_raw:
        btn = json.loads(btn_raw)
        if not btn.get("disabled"):
            print(f"\n[4] Click Generate en ({btn['x']},{btn['y']})...")
            click(ws, btn['x'], btn['y'])
            time.sleep(10)
            ss(ws, "type_result.png")

            url = js(ws, "window.location.href")
            print(f"  URL: {url}")
            page = js(ws, "document.body.innerText") or ""
            print(f"  Texto: {page[:500]}")

            key_raw = js(ws, FIND_KEY_JS)
            print(f"\n  Key search: {key_raw}")

            if key_raw and key_raw.startswith(("INPUT:", "TEXT:")):
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
                print("\n  Key no encontrada. Ver type_result.png")
        else:
            page = js(ws, "document.body.innerText") or ""
            required = [l for l in page.split("\n") if "required" in l.lower()]
            print(f"\n  Botón disabled. Campos requeridos faltantes: {required}")
            ss(ws, "type_disabled.png")
    else:
        print("  Botón Generate no encontrado")

    ws.close()


if __name__ == "__main__":
    main()
