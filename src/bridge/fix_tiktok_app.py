"""
Navega al TikTok Developer App, obtiene el Client Key correcto
y añade el Redirect URI de Composio.
python -m src.bridge.fix_tiktok_app
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
COMPOSIO_REDIRECT = "https://backend.composio.dev/api/v1/auth-apps/add"
APP_URL = "https://developers.tiktok.com/app/7640160757242218516"
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

GET_CREDENTIALS_JS = """
(function() {
    var text = document.body.innerText;
    var result = {};

    // Buscar Client Key
    var keyPatterns = [
        /Client [Kk]ey[\\s:]+([A-Za-z0-9+\\/=_-]{8,80})/,
        /[Cc]lient_?[Kk]ey[\\s:]+([A-Za-z0-9+\\/=_-]{8,80})/,
        /App [Kk]ey[\\s:]+([A-Za-z0-9+\\/=_-]{8,80})/,
    ];
    for (var i=0; i<keyPatterns.length; i++) {
        var m = text.match(keyPatterns[i]);
        if (m) { result.clientKey = m[1].trim(); break; }
    }

    // Buscar Client Secret
    var secretPatterns = [
        /Client [Ss]ecret[\\s:]+([A-Za-z0-9+\\/=_-]{16,80})/,
        /[Cc]lient_?[Ss]ecret[\\s:]+([A-Za-z0-9+\\/=_-]{16,80})/,
    ];
    for (var i=0; i<secretPatterns.length; i++) {
        var m = text.match(secretPatterns[i]);
        if (m) { result.clientSecret = m[1].trim(); break; }
    }

    // Buscar en inputs readonly
    Array.from(document.querySelectorAll("input[readonly], input[type='text'], code")).forEach(function(el) {
        var val = (el.value || el.textContent || "").trim();
        if (val.length >= 8 && val.length <= 80) {
            var container = el.closest("tr, div, li, section");
            if (container) {
                var label = container.textContent.toLowerCase();
                if ((label.includes("client key") || label.includes("app key")) && !result.clientKey) {
                    result.clientKey = val;
                }
                if (label.includes("secret") && !result.clientSecret) {
                    result.clientSecret = val;
                }
            }
        }
    });

    return JSON.stringify(result);
})()
"""


def main():
    print("=" * 60)
    print("FIX TIKTOK APP — Client Key + Redirect URI")
    print("=" * 60)

    ws = get_dev_ws()
    if not ws:
        print("No TikTok Developers tab. Abriendo...")
        req = urllib.request.Request(f"{CDP}/json/new", method="PUT", data=b"")
        with urllib.request.urlopen(req, timeout=5) as r:
            tab = json.loads(r.read())
        ws = websocket.WebSocket()
        ws.connect(tab["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")

    # Navegar al app detail
    print(f"\n[1] Navegando al app: {APP_URL}")
    cdp(ws, "Page.navigate", {"url": APP_URL})
    time.sleep(6)
    cdp(ws, "Page.bringToFront", {})
    ss(ws, "tiktok_app_detail.png")

    url = js(ws, "window.location.href")
    page = js(ws, "document.body.innerText") or ""
    print(f"  URL: {url}")
    print(f"  Contenido:\n{page[:600]}")

    # Buscar credenciales
    print("\n[2] Buscando Client Key...")
    creds_raw = js(ws, GET_CREDENTIALS_JS)
    creds = json.loads(creds_raw) if creds_raw else {}
    print(f"  Credenciales: {creds}")

    client_key = creds.get("clientKey", "")
    client_secret = creds.get("clientSecret", "")

    if client_key:
        print(f"\n  CLIENT KEY: {client_key}")
        # Guardar en .env
        content = ENV.read_text(encoding="utf-8")
        content = re.sub(r"TIKTOK_CLIENT_KEY=.*", f"TIKTOK_CLIENT_KEY={client_key}", content)
        if client_secret:
            content = re.sub(r"TIKTOK_CLIENT_SECRET=.*", f"TIKTOK_CLIENT_SECRET={client_secret}", content)
        ENV.write_text(content, encoding="utf-8")
        print("  Guardado en .env")

    # Buscar sección de Redirect URI para añadir Composio
    print(f"\n[3] Añadiendo Redirect URI de Composio...")
    print(f"  URI: {COMPOSIO_REDIRECT}")

    # Buscar el input de Redirect URI
    redirect_section = js(ws, """
    (function() {
        var text = document.body.innerText;
        if (text.includes("Redirect") || text.includes("redirect")) {
            // Buscar input o botón para añadir redirect URI
            var btns = Array.from(document.querySelectorAll("button, a"));
            var addBtn = btns.find(function(b) {
                return b.textContent.toLowerCase().includes("add") &&
                       (b.closest && b.closest("[class*='redirect'], [data-testid*='redirect']"));
            });
            var inputs = Array.from(document.querySelectorAll("input[placeholder*='redirect'], input[placeholder*='URI']"));
            if (inputs[0]) {
                var r = inputs[0].getBoundingClientRect();
                return JSON.stringify({type: "input", x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
            }
            return "redirect_section_exists";
        }
        return "no_redirect_section";
    })()
    """)
    print(f"  Redirect section: {redirect_section}")

    # Si hay un input de redirect URI, añadir
    if redirect_section and redirect_section.startswith("{"):
        inp = json.loads(redirect_section)
        click(ws, inp["x"], inp["y"])
        time.sleep(0.3)
        cdp(ws, "Input.insertText", {"text": COMPOSIO_REDIRECT})
        time.sleep(0.3)
        # Enter para confirmar
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Return", "code": "Enter"})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Return", "code": "Enter"})
        time.sleep(2)
        ss(ws, "tiktok_app_redirect_added.png")
        print("  Redirect URI añadida!")

    # Buscar la sección de productos (Content Posting API)
    print("\n[4] Buscando sección de Products...")
    products = js(ws, """
    (function() {
        var links = Array.from(document.querySelectorAll("a, button, li, [role='tab']"));
        var products = links.find(function(l) { return l.textContent.toLowerCase().includes("product"); });
        if (products) {
            var r = products.getBoundingClientRect();
            return JSON.stringify({text: products.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
        }
        return null;
    })()
    """)
    print(f"  Products: {products}")

    ss(ws, "tiktok_app_overview.png")

    # Resumen final
    print("\n" + "=" * 60)
    print("ESTADO DE LA TIKTOK APP")
    print("=" * 60)
    print(f"  App ID: 7640160757242218516")
    print(f"  Client Key: {client_key or 'VER tiktok_app_detail.png'}")
    print(f"  Client Secret: {client_secret or 'PENDIENTE'}")
    print(f"  Redirect URI requerido: {COMPOSIO_REDIRECT}")
    print(f"\n  El error 'unauthorized_client' se soluciona:")
    print(f"  1. Verificar Client Key en la app de TikTok Developers")
    print(f"  2. Añadir Redirect URI: {COMPOSIO_REDIRECT}")
    print(f"  3. Actualizar Composio Auth Config con el Client Key correcto")

    ws.close()


if __name__ == "__main__":
    main()
