"""
Click en 'Your API Key' en Pexels y extrae la key.
joan ya tiene cuenta, solo hace falta navegar y hacer click.
python -m src.bridge.pexels_click_apikey
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def open_tab():
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())["webSocketDebuggerUrl"]

def ws_connect(u):
    ws = websocket.WebSocket()
    ws.connect(u, timeout=10, origin="http://localhost:9222")
    return ws

def cdp(ws, m, p=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid: return r
        except: return None

def nav(ws, url, wait=6):
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(wait)

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


FIND_APIBTN_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("a, button"));
    var btn = btns.find(function(b) { return b.textContent.trim() === "Your API Key"; });
    if (!btn) btn = btns.find(function(b) { return b.textContent.includes("API Key"); });
    if (btn) {
        var r = btn.getBoundingClientRect();
        return JSON.stringify({
            x: Math.round(r.left + r.width/2),
            y: Math.round(r.top + r.height/2),
            href: btn.href || btn.tagName
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
        if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return v;
    }
    var all = Array.from(document.querySelectorAll("code, pre, span, p, div"));
    for (var i = 0; i < all.length; i++) {
        var t = all[i].textContent.trim();
        if (t.length >= 32 && t.length <= 64 && /^[A-Za-z0-9]+$/.test(t) &&
            all[i].children.length === 0) return t;
    }
    return null;
})()
"""


def save_key(key):
    content = ENV.read_text(encoding="utf-8")
    if "PEXELS_API_KEY" in content:
        content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
    else:
        content += f"\nPEXELS_API_KEY={key}\n"
    ENV.write_text(content, encoding="utf-8")
    print("  Guardada en .env")


def main():
    print("=" * 50)
    print("PEXELS API KEY CLICK — joan logged in")
    print("=" * 50)

    ws = ws_connect(open_tab())

    # Navegar a la página API
    print("\n[NAV] pexels.com/api/")
    nav(ws, "https://www.pexels.com/api/", wait=6)
    ss(ws, "pex_loggedin.png")

    # Verificar que está logueado
    url = js(ws, "window.location.href")
    print(f"  URL: {url}")

    # Click en "Your API Key"
    btn_raw = js(ws, FIND_APIBTN_JS)
    if btn_raw:
        btn = json.loads(btn_raw)
        print(f"\n  Click 'Your API Key' en ({btn['x']}, {btn['y']})...")
        click(ws, btn['x'], btn['y'])
        time.sleep(6)
        ss(ws, "pex_apikey_page.png")
        url = js(ws, "window.location.href")
        print(f"  URL post-click: {url}")

        # Buscar la key
        key = js(ws, FIND_KEY_JS)
        if key and len(key) >= 32:
            print(f"\n✅ PEXELS API KEY: {key}")
            save_key(key)
            ws.close()
            return

        # Si navegó a otra página, buscar key ahí
        page_text = js(ws, "document.body.innerText") or ""
        print(f"  Texto visible: {page_text[:300]}")

    # Si el botón tiene un href, navegar directamente
    print("\n  Intentando navegación directa...")
    for url in [
        "https://www.pexels.com/api/new/",
        "https://www.pexels.com/api/dashboard/",
        "https://www.pexels.com/api/?locale=en-US",
    ]:
        nav(ws, url, wait=5)
        current = js(ws, "window.location.href")
        key = js(ws, FIND_KEY_JS)
        if key and len(key) >= 32:
            print(f"\n✅ PEXELS API KEY en {current}: {key}")
            save_key(key)
            ws.close()
            return
        print(f"  {current}: no key")

    ss(ws, "pex_debug.png")

    # La API key de Pexels está en la página. Ver el screenshot pex_loggedin.png
    # El botón "Your API Key" lleva a una página donde se muestra la key
    print("\n  La página pex_apikey_page.png muestra el estado actual.")
    print("  Si el botón navegó correctamente, la key debería estar visible.")
    print("\n  ACCIÓN MÍNIMA DEL USUARIO:")
    print("  1. Mira tu Chrome - hay una pestaña abierta en pexels.com")
    print("  2. Busca el texto de la API key (es una cadena de ~32 caracteres)")
    print("  3. Cópiala y pégala aquí o corre:")
    print("     python -m src.bridge.save_env_key PEXELS_API_KEY TU_KEY")

    ws.close()


if __name__ == "__main__":
    main()
