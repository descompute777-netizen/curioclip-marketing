"""
Actualiza el Auth Config de Composio con el Client Key correcto.
Los campos estaban invertidos — ahora los ponemos en el orden correcto.
python -m src.bridge.fix_composio_authconfig
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
AUTH_CONFIG_ID = "ac_zehMCGYPXa3C"
CLIENT_KEY = "***REMOVED***"
CLIENT_SECRET = "***REMOVED***"
COMPOSIO_REDIRECT = "https://backend.composio.dev/api/v1/auth-apps/add"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_composio_ws():
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
    time.sleep(0.5)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

FIND_AND_CLICK_BTN_JS = """
(function(searchTexts) {
    var btns = Array.from(document.querySelectorAll("button, a, [role='button']"));
    for (var i=0; i<searchTexts.length; i++) {
        var b = btns.find(function(x) { return x.textContent.trim().includes(searchTexts[i]); });
        if (b) {
            var r = b.getBoundingClientRect();
            if (r.width > 0 && r.height > 0) {
                return JSON.stringify({text: b.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
            }
        }
    }
    return null;
})
"""

FILL_FIELD_JS_TEMPLATE = """
(function(labelText, value) {
    var inputs = Array.from(document.querySelectorAll("input, textarea"));
    var target = null;
    // Buscar por label cercano
    var labels = Array.from(document.querySelectorAll("label, span, p"));
    for (var i=0; i<labels.length; i++) {
        if (labels[i].textContent.toLowerCase().includes(labelText.toLowerCase())) {
            var nextInp = labels[i].closest("div,tr").querySelector("input, textarea");
            if (!nextInp) nextInp = labels[i].nextElementSibling;
            if (nextInp && nextInp.tagName === "INPUT") { target = nextInp; break; }
        }
    }
    // Fallback: usar posición
    if (!target) {
        inputs = inputs.filter(function(i) { return i.getBoundingClientRect().height > 0; });
        if (labelText.toLowerCase().includes("key") || labelText.toLowerCase().includes("id")) {
            target = inputs[0];
        } else if (labelText.toLowerCase().includes("secret")) {
            target = inputs[1];
        }
    }
    if (!target) return "NOT FOUND: " + labelText;
    target.focus();
    target.select();
    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    if (setter) setter.call(target, value);
    target.value = value;
    ["input","change"].forEach(function(e) { target.dispatchEvent(new Event(e,{bubbles:true})); });
    return "SET: " + target.value.slice(0,15);
})
"""


def main():
    print("=" * 60)
    print("FIX COMPOSIO AUTH CONFIG — Correct Client Key")
    print(f"Client Key: {CLIENT_KEY}")
    print(f"Client Secret: {CLIENT_SECRET[:8]}...")
    print("=" * 60)

    ws = get_composio_ws()
    if not ws:
        print("No Composio tab"); return

    # Navegar al Auth Config
    url = f"https://dashboard.composio.dev/descompute777_workspace/descompute777_workspace_first_project/auth-configs/{AUTH_CONFIG_ID}"
    print(f"\n[1] Navegando al Auth Config {AUTH_CONFIG_ID}...")
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(6)
    cdp(ws, "Page.bringToFront", {})
    ss(ws, "fix_1_authconfig.png")

    # Buscar y click en "Manage Config"
    print("\n[2] Click en Manage Config...")
    manage_raw = js(ws, f"({FIND_AND_CLICK_BTN_JS})(['Manage Config', 'Edit', 'Configure'])")
    if manage_raw:
        manage = json.loads(manage_raw)
        print(f"  Click '{manage['text']}' en ({manage['x']},{manage['y']})")
        click(ws, manage["x"], manage["y"])
        time.sleep(5)
        ss(ws, "fix_2_manage.png")
        page = js(ws, "document.body.innerText") or ""
        print(f"  Página: {page[:400]}")

        # Buscar campos y rellenar
        print(f"\n[3] Seteando Client Key = {CLIENT_KEY}...")
        key_result = js(ws, f"({FILL_FIELD_JS_TEMPLATE})('client key', '{CLIENT_KEY}')")
        print(f"  Key: {key_result}")
        time.sleep(0.5)
        # InsertText también
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp(ws, "Input.insertText", {"text": CLIENT_KEY})
        time.sleep(0.3)

        print(f"\n[4] Seteando Client Secret...")
        secret_result = js(ws, f"({FILL_FIELD_JS_TEMPLATE})('secret', '{CLIENT_SECRET}')")
        print(f"  Secret: {secret_result}")
        time.sleep(0.3)

        ss(ws, "fix_3_filled.png")

        # Guardar
        print("\n[5] Guardando...")
        save_raw = js(ws, f"({FIND_AND_CLICK_BTN_JS})(['Save', 'Update', 'Submit', 'Confirm'])")
        if save_raw:
            save = json.loads(save_raw)
            print(f"  Click '{save['text']}'")
            click(ws, save["x"], save["y"])
            time.sleep(4)
            ss(ws, "fix_4_saved.png")
            final_page = js(ws, "document.body.innerText") or ""
            print(f"  Post-save: {final_page[:300]}")
            print("\n✅ Auth Config actualizado!")
        else:
            print("  No se encontró botón Save. Ver fix_3_filled.png")
    else:
        print("  Manage Config no encontrado")
        ss(ws, "fix_no_manage.png")
        page = js(ws, "document.body.innerText") or ""
        print(f"  Página: {page[:300]}")

    ws.close()


if __name__ == "__main__":
    main()
