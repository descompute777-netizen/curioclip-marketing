"""
Llena el formulario "Create app" de TikTok Developers.
App name: CurioClip | App type: Other
python -m src.bridge.fill_tiktok_appform
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def gws():
    with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "developers.tiktok.com" in t.get("url", ""):
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


FIND_NAME_INPUT_JS = """
(function() {
    var inp = document.querySelector('input[placeholder="Enter name"]')
           || document.querySelector('input[type="text"]:not([type="radio"])');
    if (inp) {
        var r = inp.getBoundingClientRect();
        return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
    }
    return null;
})()
"""

FIND_OTHER_RADIO_JS = """
(function() {
    var radios = Array.from(document.querySelectorAll('input[type="radio"]'));
    var other = radios.find(function(r) { return (r.value||"").toLowerCase() === "other"; });
    if (!other) other = radios[0];
    if (other) {
        var r = other.getBoundingClientRect();
        return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2), val: other.value});
    }
    return null;
})()
"""

FIND_CREATE_BTN_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button"));
    var b = btns.find(function(x) { return x.textContent.trim() === "Create app"; });
    if (!b) b = btns.find(function(x) { return x.textContent.includes("Create"); });
    if (b) {
        var r = b.getBoundingClientRect();
        return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2), text: b.textContent.trim(), disabled: b.disabled});
    }
    return null;
})()
"""

FIND_CLIENT_KEY_JS = """
(function() {
    var text = document.body.innerText;
    var all = Array.from(document.querySelectorAll("*"));
    for (var i = 0; i < all.length; i++) {
        var t = all[i].textContent.trim();
        // Client key format: 7 chars or longer alphanumeric
        if (t.length >= 8 && t.length <= 40 && /^[A-Za-z0-9_-]+$/.test(t) && all[i].children.length === 0) {
            var parent = all[i].closest("tr,li,div");
            if (parent) {
                var parentText = parent.textContent.toLowerCase();
                if (parentText.includes("client") || parentText.includes("key") || parentText.includes("id")) {
                    return "FOUND:" + t;
                }
            }
        }
    }
    // Search in full page text with regex
    var m = text.match(/Client [Kk]ey[\\s\\S]{0,20}?([A-Za-z0-9_-]{8,40})/);
    if (m) return "REGEX:" + m[1];
    return null;
})()
"""


def main():
    print("=" * 60)
    print("FILL TIKTOK APP FORM — CurioClip")
    print("=" * 60)

    ws = gws()
    if not ws:
        print("No se encontró la pestaña de TikTok Developers")
        return

    cdp(ws, "Page.bringToFront", {})
    time.sleep(1)
    ss(ws, "form_initial.png")

    page = js(ws, "document.body.innerText") or ""
    print(f"Estado actual: {page[:200]}")

    # PASO 1: App name
    print("\n[1] App name = CurioClip")
    name_coords = js(ws, FIND_NAME_INPUT_JS)
    if name_coords:
        nc = json.loads(name_coords)
        click(ws, nc["x"], nc["y"])
        time.sleep(0.2)
        # Ctrl+A → Delete → InsertText
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete", "code": "Delete"})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Delete", "code": "Delete"})
        cdp(ws, "Input.insertText", {"text": "CurioClip"})
        time.sleep(0.3)
        print(f"  Filled at ({nc['x']},{nc['y']})")
    else:
        print("  Input not found — intentando click en coordenada fija")
        click(ws, 770, 207)
        time.sleep(0.2)
        cdp(ws, "Input.insertText", {"text": "CurioClip"})

    # PASO 2: App type = Other
    print("\n[2] App type = Other")
    other = js(ws, FIND_OTHER_RADIO_JS)
    if other:
        od = json.loads(other)
        print(f"  Radio '{od.get('val')}' en ({od['x']},{od['y']})")
        click(ws, od["x"], od["y"])
    else:
        print("  Radio no encontrado — click en coordenada fija")
        click(ws, 490, 327)

    time.sleep(0.3)
    ss(ws, "form_filled.png")

    # PASO 3: Create app
    print("\n[3] Click Create app")
    create_raw = js(ws, FIND_CREATE_BTN_JS)
    if create_raw:
        cd = json.loads(create_raw)
        print(f"  '{cd['text']}' disabled={cd.get('disabled')} en ({cd['x']},{cd['y']})")
        click(ws, cd["x"], cd["y"])
    else:
        print("  Botón no encontrado — click en coordenada fija")
        click(ws, 1025, 436)

    print("  Esperando respuesta...")
    time.sleep(8)
    ss(ws, "app_created.png")

    url = js(ws, "window.location.href")
    page2 = js(ws, "document.body.innerText") or ""
    print(f"\n  URL: {url}")
    print(f"  Contenido: {page2[:800]}")

    # PASO 4: Buscar credenciales
    print("\n[4] Buscando Client Key...")
    key_raw = js(ws, FIND_CLIENT_KEY_JS)
    print(f"  Key search: {key_raw}")

    # Si no hay key, navegar al detalle de la app
    if not key_raw:
        # Buscar link a la app recién creada
        app_link = js(ws, """
        (function() {
            var links = Array.from(document.querySelectorAll("a"));
            var app = links.find(function(l) {
                return l.href && l.href.includes("/apps/") && !l.href.includes("#");
            });
            return app ? app.href : null;
        })()
        """)
        if app_link:
            print(f"  Navegando a app: {app_link}")
            cdp(ws, "Page.navigate", {"url": app_link})
            time.sleep(5)
            ss(ws, "app_detail.png")
            page3 = js(ws, "document.body.innerText") or ""
            print(f"  App detail: {page3[:800]}")
            key_raw = js(ws, FIND_CLIENT_KEY_JS)
            print(f"  Key en detail: {key_raw}")

    if key_raw and ":" in key_raw:
        client_key = key_raw.split(":", 1)[1]
        print(f"\n✅ CLIENT KEY: {client_key}")
        content = ENV.read_text(encoding="utf-8")
        if "TIKTOK_CLIENT_KEY" not in content:
            content += f"\nTIKTOK_CLIENT_KEY={client_key}\n"
            ENV.write_text(content, encoding="utf-8")
            print("  Guardado en .env")

    ws.close()


if __name__ == "__main__":
    main()
