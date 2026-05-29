"""
Corrige el Client ID duplicado en Composio y guarda.
python -m src.bridge.fix_client_id
"""
import os, sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY", "")
if not CLIENT_KEY:
    sys.exit("Define TIKTOK_CLIENT_KEY en el entorno (.env)")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def gws():
    with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "composio" in t.get("url", "").lower():
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
            return ws

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

FIX_CLIENT_ID_JS = """
(function() {
    var inputs = Array.from(document.querySelectorAll("input"));
    var target = null;
    // Buscar el campo que tiene el valor duplicado
    for (var i=0; i<inputs.length; i++) {
        var val = inputs[i].value || "";
        if (val.toLowerCase().includes("client") || val.length > 15) {
            // Verificar si es el campo de Client ID (no password)
            if (inputs[i].type !== "password") {
                target = inputs[i];
                break;
            }
        }
    }
    if (!target && inputs.length > 0) {
        // Primer input visible que no sea password
        target = inputs.find(function(i) { return i.type !== "password" && i.getBoundingClientRect().height > 0; });
    }
    if (!target) return "NOT FOUND";

    target.focus();
    target.select();
    // Usar setter nativo para limpiar
    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    setter.call(target, window.__CLIENT_KEY || "");
    target.dispatchEvent(new Event("input", {bubbles:true}));
    target.dispatchEvent(new Event("change", {bubbles:true}));

    var r = target.getBoundingClientRect();
    return JSON.stringify({
        old_val: target.value,
        x: Math.round(r.left + r.width/2),
        y: Math.round(r.top + r.height/2)
    });
})()
"""

FIND_SAVE_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button"));
    var b = btns.find(function(x) { return x.textContent.trim() === "Save"; });
    if (!b) b = btns.find(function(x) { return x.textContent.toLowerCase().includes("save"); });
    if (b) {
        var r = b.getBoundingClientRect();
        return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
    }
    return null;
})()
"""


def main():
    print("=" * 60)
    print("FIX CLIENT ID → " + CLIENT_KEY)
    print("=" * 60)

    ws = gws()
    if not ws:
        print("No Composio tab"); return

    cdp(ws, "Page.bringToFront", {})
    ss(ws, "before_fix.png")

    # Corregir el Client ID
    print("\n[1] Seteando Client ID correcto...")
    fix_raw = js(ws, FIX_CLIENT_ID_JS)
    print(f"  Result: {fix_raw}")

    if fix_raw and fix_raw != "NOT FOUND":
        try:
            fix_data = json.loads(fix_raw)
            print(f"  Value set: {fix_data.get('old_val', '?')}")
            # Click en el campo y usar insertText para React
            click(ws, fix_data.get("x", 370), fix_data.get("y", 300))
            time.sleep(0.2)
            cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
            cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
            cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete", "code": "Delete"})
            cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Delete", "code": "Delete"})
            cdp(ws, "Input.insertText", {"text": CLIENT_KEY})
            time.sleep(0.3)
        except json.JSONDecodeError:
            print(f"  Parse: {fix_raw}")
    else:
        print("  Input no encontrado. Intentando click en coordenada del campo...")
        click(ws, 370, 300)
        time.sleep(0.2)
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete", "code": "Delete"})
        cdp(ws, "Input.insertText", {"text": CLIENT_KEY})

    time.sleep(0.5)
    ss(ws, "after_fix.png")

    # Guardar
    print("\n[2] Guardando...")
    save_raw = js(ws, FIND_SAVE_JS)
    if save_raw:
        save = json.loads(save_raw)
        print(f"  Click Save en ({save['x']},{save['y']})")
        click(ws, save["x"], save["y"])
        time.sleep(5)
        ss(ws, "fix_saved.png")
        page = js(ws, "document.body.innerText") or ""
        print(f"  Post-save: {page[:300]}")
        print("\n✅ Auth Config guardado con Client Key correcto!")
    else:
        print("  Botón Save no encontrado. Ver after_fix.png")

    ws.close()


if __name__ == "__main__":
    main()
