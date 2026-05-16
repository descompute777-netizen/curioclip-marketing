"""
Añade el Redirect URI de Composio en la TikTok Developer App
a través del producto Login Kit.
python -m src.bridge.add_tiktok_redirect_uri
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
APP_URL = "https://developers.tiktok.com/app/7640160757242218516"
REDIRECT_URI = "https://backend.composio.dev/api/v1/auth-apps/add"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_dev_ws():
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

FIND_BTN_JS_TEMPLATE = """
(function(searchTexts) {
    var all = Array.from(document.querySelectorAll("button, a, li, [role='tab'], [role='menuitem']"));
    for (var i=0; i<searchTexts.length; i++) {
        var el = all.find(function(x) {
            return x.textContent.trim().toLowerCase().includes(searchTexts[i].toLowerCase());
        });
        if (el) {
            var r = el.getBoundingClientRect();
            if (r.width > 0 && r.height > 0) {
                return JSON.stringify({text: el.textContent.trim().slice(0,30), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
            }
        }
    }
    return null;
})
"""


def main():
    print("=" * 60)
    print("ADD REDIRECT URI TO TIKTOK DEVELOPER APP")
    print(f"URI: {REDIRECT_URI}")
    print("=" * 60)

    ws = get_dev_ws()
    if not ws:
        print("No TikTok Developers tab — abriendo nueva...")
        req = urllib.request.Request(f"{CDP}/json/new", method="PUT", data=b"")
        with urllib.request.urlopen(req, timeout=5) as r:
            tab = json.loads(r.read())
        ws = websocket.WebSocket()
        ws.connect(tab["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")

    # Navegar al app
    print(f"\n[1] Navegando al App: {APP_URL}")
    cdp(ws, "Page.navigate", {"url": f"{APP_URL}/sandbox"})
    time.sleep(5)
    cdp(ws, "Page.bringToFront", {})
    ss(ws, "app_nav.png")

    url = js(ws, "window.location.href")
    page = js(ws, "document.body.innerText") or ""
    print(f"  URL: {url}")
    print(f"  Contenido: {page[:300]}")

    # Ir a Products
    print("\n[2] Click en Products (sidebar)...")
    products_raw = js(ws, f"({FIND_BTN_JS_TEMPLATE})(['Products', 'Login Kit', 'Product'])")
    if products_raw:
        prod = json.loads(products_raw)
        print(f"  Click '{prod['text']}' en ({prod['x']},{prod['y']})")
        click(ws, prod["x"], prod["y"])
        time.sleep(4)
        ss(ws, "products_page.png")
        page2 = js(ws, "document.body.innerText") or ""
        print(f"  Página Products: {page2[:400]}")

        # Añadir Login Kit si no está
        if "Login Kit" not in page2:
            print("\n  Añadiendo Login Kit...")
            add_kit = js(ws, f"({FIND_BTN_JS_TEMPLATE})(['Add products', 'Add product', 'Login Kit'])")
            if add_kit:
                ak = json.loads(add_kit)
                click(ws, ak["x"], ak["y"])
                time.sleep(3)
                ss(ws, "add_kit.png")

        # Buscar campo de Redirect URI dentro de Login Kit
        print("\n  Buscando campo Redirect URI en Login Kit...")
        redirect_input = js(ws, """
        (function() {
            var inputs = Array.from(document.querySelectorAll("input[type='url'], input[type='text'], input[placeholder*='redirect'], input[placeholder*='http']"));
            var ri = inputs.find(function(i) {
                var ph = (i.placeholder || "").toLowerCase();
                return ph.includes("redirect") || ph.includes("uri") || ph.includes("http");
            });
            if (ri) {
                var r = ri.getBoundingClientRect();
                return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2), ph: ri.placeholder});
            }
            return null;
        })()
        """)
        print(f"  Redirect input: {redirect_input}")

        if redirect_input:
            ri = json.loads(redirect_input)
            click(ws, ri["x"], ri["y"])
            time.sleep(0.3)
            cdp(ws, "Input.insertText", {"text": REDIRECT_URI})
            time.sleep(0.3)
            # Buscar Add button
            add_btn = js(ws, f"({FIND_BTN_JS_TEMPLATE})(['Add', 'Save', 'Confirm'])")
            if add_btn:
                ab = json.loads(add_btn)
                click(ws, ab["x"], ab["y"])
                time.sleep(2)
                ss(ws, "redirect_added.png")
                print(f"  ✅ Redirect URI añadida!")

    # Intentar también en la sección de "Scopes" o directamente en la app
    # El redirect URI suele estar en "Configure" de cada producto
    print("\n[3] Verificando estado final de la app...")
    cdp(ws, "Page.navigate", {"url": f"{APP_URL}/sandbox"})
    time.sleep(5)
    ss(ws, "app_final.png")
    page_final = js(ws, "document.body.innerText") or ""
    print(f"  Estado final: {page_final[:400]}")

    print(f"\nEl Redirect URI a configurar en TikTok Developers es:")
    print(f"  {REDIRECT_URI}")
    print(f"\nSi el OAuth sigue fallando, ve manualmente a:")
    print(f"  https://developers.tiktok.com/app/7640160757242218516")
    print(f"  → Sandbox → Products → Login Kit → Redirect URI")
    print(f"  → Añade: {REDIRECT_URI}")

    ws.close()


if __name__ == "__main__":
    main()
