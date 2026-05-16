"""
Login en TikTok for Developers y obtiene credenciales de la app.
python -m src.bridge.tiktok_dev_login
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_tab_ws(url_fragment):
    with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if url_fragment in t.get("url", ""):
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
            return ws, t["url"]
    return None, None

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

def main():
    print("=== TIKTOK DEVELOPERS LOGIN ===\n")

    ws, url = get_tab_ws("developers.tiktok.com")
    if not ws:
        print("Tab no encontrada. Abriendo nueva...")
        req = urllib.request.Request(f"{CDP}/json/new", method="PUT", data=b"")
        with urllib.request.urlopen(req, timeout=5) as r:
            tab = json.loads(r.read())
        ws = websocket.WebSocket()
        ws.connect(tab["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
        cdp(ws, "Page.navigate", {"url": "https://developers.tiktok.com/apps/"})
        time.sleep(5)

    cdp(ws, "Page.bringToFront", {})
    time.sleep(1)

    current_url = js(ws, "window.location.href")
    print(f"URL actual: {current_url}")

    # Buscar y hacer click en el botón Login
    login_btn = js(ws, """
    (function() {
        var btns = Array.from(document.querySelectorAll("button, a"));
        var btn = btns.find(function(b) {
            return b.textContent.trim() === "Login" || b.textContent.trim() === "Log in";
        });
        if (btn) {
            var r = btn.getBoundingClientRect();
            return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2), text: btn.textContent.trim()});
        }
        return null;
    })()
    """)
    print(f"Botón Login: {login_btn}")

    if login_btn:
        data = json.loads(login_btn)
        print(f"Click en '{data['text']}' ({data['x']},{data['y']})...")
        click(ws, data['x'], data['y'])
        time.sleep(8)  # Esperar redirección OAuth de TikTok

        ss(ws, "dev_after_login.png")
        url_after = js(ws, "window.location.href")
        page_after = js(ws, "document.body.innerText") or ""
        print(f"URL post-login: {url_after}")
        print(f"Texto: {page_after[:300]}")

        # Si llegamos a los apps, buscar credenciales
        if "apps" in url_after.lower() and "No access" not in page_after:
            print("\n✅ Logueado en TikTok Developers!")
            extract_credentials(ws)
        elif "tiktok.com" in url_after:
            print("\nRedirigido a TikTok para autenticación...")
            time.sleep(8)
            ss(ws, "dev_tiktok_auth.png")
            url2 = js(ws, "window.location.href")
            page2 = js(ws, "document.body.innerText") or ""
            print(f"URL: {url2}")
            print(f"Texto: {page2[:300]}")
            if "developers.tiktok.com" in url2:
                extract_credentials(ws)
    else:
        # Ya podría estar logueado, intentar acceder directamente
        print("No se encontró botón Login. Verificando estado...")
        page = js(ws, "document.body.innerText") or ""
        print(f"Página: {page[:300]}")
        ss(ws, "dev_current.png")
        if "No access" not in page:
            extract_credentials(ws)

    ws.close()


def extract_credentials(ws):
    """Extrae Client Key y Client Secret de la app existente o la crea."""
    print("\n=== EXTRAYENDO CREDENCIALES ===")

    cdp(ws, "Page.navigate", {"url": "https://developers.tiktok.com/apps/"})
    time.sleep(5)
    ss(ws, "dev_apps_list.png")

    page = js(ws, "document.body.innerText") or ""
    print(f"Apps page: {page[:500]}")

    # Buscar Client Key o Client ID en la página
    key_found = js(ws, """
    (function() {
        var text = document.body.innerText;
        var patterns = [
            /Client [Kk]ey[:\\s]+([A-Za-z0-9_-]{10,})/,
            /Client [Ii][Dd][:\\s]+([A-Za-z0-9_-]{10,})/,
            /App [Kk]ey[:\\s]+([A-Za-z0-9_-]{10,})/
        ];
        for (var i=0; i<patterns.length; i++) {
            var m = text.match(patterns[i]);
            if (m) return m[1];
        }
        return null;
    })()
    """)

    if key_found:
        print(f"\n✅ Client Key encontrado: {key_found}")
    else:
        print("No se encontró Client Key en la página de apps.")
        # Intentar hacer click en una app para ver sus detalles
        app_link = js(ws, """
        (function() {
            var links = Array.from(document.querySelectorAll("a"));
            var app = links.find(function(l) {
                return l.href.includes("/apps/") && !l.href.endsWith("/apps/");
            });
            if (app) return JSON.stringify({href: app.href, text: app.textContent.trim()});
            // Buscar botones de apps
            var btns = Array.from(document.querySelectorAll("button, [role=button]"));
            var appBtn = btns.find(function(b) { return b.textContent.toLowerCase().includes("curioclip"); });
            if (!appBtn) appBtn = btns.find(function(b) { return b.textContent.trim().length > 2; });
            if (appBtn) {
                var r = appBtn.getBoundingClientRect();
                return JSON.stringify({text: appBtn.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
            }
            return null;
        })()
        """)
        print(f"App encontrada: {app_link}")
        if app_link:
            app_data = json.loads(app_link)
            if "href" in app_data:
                cdp(ws, "Page.navigate", {"url": app_data["href"]})
                time.sleep(5)
                ss(ws, "dev_app_detail.png")
                page2 = js(ws, "document.body.innerText") or ""
                print(f"App detail: {page2[:500]}")


if __name__ == "__main__":
    main()
