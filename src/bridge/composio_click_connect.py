"""
Llena User ID y hace click en Connect para iniciar TikTok OAuth en Composio.
python -m src.bridge.composio_click_connect
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
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

SET_USERID_JS = """
(function() {
    var inp = document.querySelector("input[type='text'], input:not([type='radio']):not([type='checkbox'])");
    if (inp) {
        inp.focus();
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        setter.call(inp, "curioclip");
        inp.dispatchEvent(new Event("input", {bubbles:true}));
        inp.dispatchEvent(new Event("change", {bubbles:true}));
        return inp.value;
    }
    return "no input found";
})()
"""

FIND_CONNECT_BTN_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button"));
    var b = btns.find(function(x) { return x.textContent.trim() === "Connect"; });
    if (b) {
        var r = b.getBoundingClientRect();
        return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
    }
    return null;
})()
"""

FIND_AUTHORIZE_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button, [role='button'], a"));
    var keywords = ["authorize", "allow", "confirm", "accept", "login", "log in"];
    var a = btns.find(function(b) {
        return keywords.some(function(k) { return b.textContent.toLowerCase().includes(k); });
    });
    if (a) {
        var r = a.getBoundingClientRect();
        return JSON.stringify({text: a.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
    }
    return null;
})()
"""


def main():
    print("=" * 60)
    print("COMPOSIO → CONNECT BUTTON → TIKTOK OAUTH")
    print("=" * 60)

    ws = gws()
    if not ws:
        print("No Composio tab"); return

    cdp(ws, "Page.bringToFront", {})
    ss(ws, "conn_0_before.png")

    # Paso 1: Set User ID
    print("\n[1] Seteando User ID = curioclip...")
    uid_result = js(ws, SET_USERID_JS)
    print(f"  Result: {uid_result}")
    time.sleep(0.3)
    # También con insertText por si React no detectó el setter
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete", "code": "Delete"})
    cdp(ws, "Input.insertText", {"text": "curioclip"})
    time.sleep(0.3)

    # Paso 2: Click Connect
    print("\n[2] Click Connect...")
    connect_raw = js(ws, FIND_CONNECT_BTN_JS)
    if connect_raw:
        conn = json.loads(connect_raw)
        print(f"  Click en ({conn['x']},{conn['y']})")
        click(ws, conn["x"], conn["y"])
    else:
        print("  Botón no encontrado, click en coordenada fija (529, 437)")
        click(ws, 529, 437)

    # Esperar respuesta (OAuth puede abrirse en misma pestaña o nueva)
    print("  Esperando OAuth...")
    time.sleep(10)
    ss(ws, "conn_1_oauth.png")

    url = js(ws, "window.location.href")
    page = js(ws, "document.body.innerText") or ""
    print(f"\n  URL: {url}")
    print(f"  Contenido: {page[:300]}")

    # Si TikTok OAuth se abrió
    if "tiktok.com" in url.lower():
        print("\n✅ TikTok OAuth abierto!")
        time.sleep(3)
        auth_raw = js(ws, FIND_AUTHORIZE_JS)
        if auth_raw:
            auth = json.loads(auth_raw)
            btn_text = auth.get("text", "?")
            btn_x = auth.get("x", 0)
            btn_y = auth.get("y", 0)
            print(f"  Auto-click Authorize: '{btn_text}' en ({btn_x},{btn_y})")
            click(ws, btn_x, btn_y)
            time.sleep(10)
            ss(ws, "conn_2_done.png")
            final_url = js(ws, "window.location.href")
            print(f"  URL final: {final_url}")
            if "composio" in final_url:
                print("\n✅ ¡TikTok OAuth COMPLETADO exitosamente!")
        else:
            print("  No se encontró botón de Authorize. El OAuth puede necesitar login manual.")
            print("  Ver conn_1_oauth.png para el estado.")
    elif "composio" in url and "auth-configs" in url:
        print("\n  Redirigido de vuelta a Composio.")
        print(f"  Texto visible: {page[:400]}")
        # Verificar si hay una conexión activa ahora
        if "ACTIVE" in page or "Active" in page or "connected" in page.lower():
            print("✅ Conexión TikTok ACTIVA en Composio!")
        else:
            print("  Estado de conexión no confirmado. Ver conn_1_oauth.png")
    else:
        print(f"  URL inesperada. Ver conn_1_oauth.png")

    ws.close()


if __name__ == "__main__":
    main()
