"""
Limpia completamente el Client ID y lo setea correctamente.
Usa solo insertText (un solo método, sin native setter).
python -m src.bridge.clear_and_set_client_id
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
CLIENT_KEY = "***REMOVED***"
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
    time.sleep(0.3)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

FIND_CLIENT_ID_FIELD_JS = """
(function() {
    var inputs = Array.from(document.querySelectorAll("input[type='text'], input:not([type='password'])"));
    var target = inputs.find(function(i) {
        var r = i.getBoundingClientRect();
        return r.height > 0 && r.width > 100 && i.type !== "password";
    });
    if (target) {
        target.focus();
        var r = target.getBoundingClientRect();
        return JSON.stringify({
            currentValue: target.value,
            x: Math.round(r.left + r.width/2),
            y: Math.round(r.top + r.height/2)
        });
    }
    return null;
})()
"""

FIND_SAVE_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button"));
    var b = btns.find(function(x) { return x.textContent.trim() === "Save"; });
    if (b) {
        var r = b.getBoundingClientRect();
        return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
    }
    return null;
})()
"""


def main():
    print("=" * 60)
    print("CLEAR AND SET CLIENT ID → " + CLIENT_KEY)
    print("=" * 60)

    ws = gws()
    if not ws:
        print("No Composio tab"); return

    cdp(ws, "Page.bringToFront", {})

    # Encontrar el campo Client ID
    print("\n[1] Localizando campo Client ID...")
    field_raw = js(ws, FIND_CLIENT_ID_FIELD_JS)
    if not field_raw:
        print("  Campo no encontrado"); ws.close(); return

    field = json.loads(field_raw)
    print(f"  Valor actual: '{field.get('currentValue', '?')}'")
    print(f"  Posición: ({field['x']},{field['y']})")

    # Click triple en el campo para seleccionar todo
    print("\n[2] Seleccionando todo y borrando...")
    click(ws, field["x"], field["y"])
    time.sleep(0.2)
    # Triple click selecciona todo el texto
    for t in ["mousePressed", "mouseReleased"]:
        cdp(ws, "Input.dispatchMouseEvent", {"type": t, "x": field["x"], "y": field["y"],
                                              "button": "left", "clickCount": 3})
    time.sleep(0.2)
    # Borrar selección
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace"})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace"})
    time.sleep(0.2)

    # Verificar que está vacío
    val_check = js(ws, """
    (function() {
        var inputs = Array.from(document.querySelectorAll("input:not([type='password'])"));
        var target = inputs.find(function(i) { return i.getBoundingClientRect().height > 0; });
        return target ? target.value : "no field";
    })()
    """)
    print(f"  Valor después de borrar: '{val_check}'")

    # Insertar el Client Key correcto (solo InsertText, sin native setter)
    print(f"\n[3] Insertando '{CLIENT_KEY}'...")
    cdp(ws, "Input.insertText", {"text": CLIENT_KEY})
    time.sleep(0.5)

    # Verificar
    val_after = js(ws, """
    (function() {
        var inputs = Array.from(document.querySelectorAll("input:not([type='password'])"));
        var target = inputs.find(function(i) { return i.getBoundingClientRect().height > 0; });
        return target ? target.value : "no field";
    })()
    """)
    print(f"  Valor final: '{val_after}'")
    ss(ws, "client_id_set.png")

    if val_after == CLIENT_KEY:
        print(f"  ✅ Client ID correcto: {val_after}")
    else:
        print(f"  ⚠️ Valor inesperado: {val_after}")

    # Guardar
    print("\n[4] Guardando...")
    save_raw = js(ws, FIND_SAVE_JS)
    if save_raw:
        save = json.loads(save_raw)
        click(ws, save["x"], save["y"])
        time.sleep(5)
        ss(ws, "client_id_saved.png")
        page = js(ws, "document.body.innerText") or ""
        print(f"  Post-save: {page[:200]}")
        print("\n✅ Composio Auth Config actualizado correctamente!")
    else:
        print("  Save no encontrado")

    ws.close()


if __name__ == "__main__":
    main()
