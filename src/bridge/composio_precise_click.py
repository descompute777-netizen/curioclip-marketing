"""
Navegación precisa en Composio usando coordenadas reales del DOM.
Obtiene el bounding rect de cada elemento y usa CDP mouse events.

python -m src.bridge.composio_precise_click
"""
import sys, json, time, urllib.request, base64
sys.stdout.reconfigure(encoding='utf-8')
import websocket

CDP_URL = "http://localhost:9222"
WORKSPACE = "descompute777_workspace"
PROJECT = "descompute777_workspace_first_project"
BASE_URL = f"https://dashboard.composio.dev/{WORKSPACE}/{PROJECT}"
_ID = [0]


def _id():
    _ID[0] += 1
    return _ID[0]

def ws_connect(ws_url):
    ws = websocket.WebSocket()
    ws.connect(ws_url, timeout=10, origin="http://localhost:9222")
    return ws

def get_composio_tab_ws():
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    pages = [t for t in tabs if t.get("type") == "page"]
    for t in pages:
        if "composio" in t.get("url", "").lower() or "dashboard" in t.get("url", "").lower():
            return t["webSocketDebuggerUrl"]
    # Nueva pestaña
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())["webSocketDebuggerUrl"]

def cdp(ws, method, params=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid:
                return r
        except Exception:
            return None
    return None

def mouse_click(ws, x, y):
    for etype in ["mousePressed", "mouseReleased"]:
        cdp(ws, "Input.dispatchMouseEvent", {
            "type": etype, "x": x, "y": y,
            "button": "left", "clickCount": 1,
            "modifiers": 0
        })
    time.sleep(0.05)

def nav(ws, url, wait=5):
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(wait)

def js_eval(ws, code, await_p=False):
    r = cdp(ws, "Runtime.evaluate", {
        "expression": code, "returnByValue": True, "awaitPromise": await_p
    })
    return (r or {}).get("result", {}).get("result", {}).get("value")

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"  📸 {path}")

def click_element_by_text(ws, text):
    """Encuentra el elemento por texto, obtiene su rect real y hace click con CDP."""
    code = f"""
    (function() {{
        const all = [...document.querySelectorAll('a, button, [role=button], li, nav *')];
        const el = all.find(e => {{
            const t = e.textContent.trim();
            return t === {json.dumps(text)} || t.startsWith({json.dumps(text)});
        }});
        if (!el) return null;
        const rect = el.getBoundingClientRect();
        return JSON.stringify({{
            text: el.textContent.trim().substring(0, 50),
            x: Math.round(rect.left + rect.width/2),
            y: Math.round(rect.top + rect.height/2),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
        }});
    }})()
    """
    result = js_eval(ws, code)
    if result:
        try:
            data = json.loads(result)
            print(f"  Elemento: '{data['text']}' en ({data['x']}, {data['y']})")
            mouse_click(ws, data['x'], data['y'])
            return data
        except Exception as e:
            print(f"  Parse error: {e}: {result}")
    return None


def cur_url(ws):
    return js_eval(ws, "window.location.href") or ""


def main():
    print("="*60)
    print("COMPOSIO TIKTOK — Precise Click Navigation")
    print("="*60)

    ws_url = get_composio_tab_ws()
    ws = ws_connect(ws_url)

    # Navegar al dashboard (Users page donde sabemos que funciona)
    print(f"\n[NAV] {BASE_URL}/users")
    nav(ws, f"{BASE_URL}/users", wait=6)
    ss(ws, "precise_1_users.png")
    print(f"  URL: {cur_url(ws)}")

    # STEP 1: Click en "sarah_user" para ver sus conexiones
    print("\n[CLICK] sarah_user...")
    result = click_element_by_text(ws, "sarah_user")
    if result:
        time.sleep(4)
        ss(ws, "precise_2_sarah.png")
        url = cur_url(ws)
        print(f"  URL: {url}")

        # Ver si TikTok está conectado
        page_text = js_eval(ws, "document.body.innerText") or ""
        tiktok_connected = "tiktok" in page_text.lower()
        print(f"  TikTok mencionado: {tiktok_connected}")

        if "tiktok" in page_text.lower():
            print("  TikTok podría estar ya conectado para este usuario")

    # STEP 2: Ir a Auth Configs directamente por URL
    print(f"\n[NAV] Auth Configs...")
    for auth_url in [
        f"{BASE_URL}/auth-configs",
        f"{BASE_URL}/auth_configs",
        f"https://dashboard.composio.dev/{WORKSPACE}/{PROJECT}/auth-configs",
    ]:
        nav(ws, auth_url, wait=5)
        url = cur_url(ws)
        print(f"  URL: {url}")
        if "auth" in url:
            break

    ss(ws, "precise_3_auth_configs.png")

    # Buscar TikTok o botón para agregar
    page_text = js_eval(ws, "document.body.innerText") or ""
    print(f"  Texto: {page_text[:200]}")

    if "tiktok" in page_text.lower():
        result = click_element_by_text(ws, "TikTok")
        if not result:
            result = click_element_by_text(ws, "tiktok")
        time.sleep(4)
        ss(ws, "precise_4_tiktok.png")

    # STEP 3: Usar el Playground de Composio para conectar TikTok
    print(f"\n[NAV] Playground (para conectar apps)...")
    nav(ws, f"{BASE_URL}/playground", wait=6)
    ss(ws, "precise_5_playground.png")
    url = cur_url(ws)
    print(f"  URL: {url}")
    page_text = js_eval(ws, "document.body.innerText") or ""
    print(f"  Texto: {page_text[:300]}")

    # STEP 4: Intentar crear auth config para TikTok
    print(f"\n[NAV] Crear Auth Config TikTok...")
    for create_url in [
        f"{BASE_URL}/auth-configs/new",
        f"{BASE_URL}/auth-configs/create",
        f"https://app.composio.dev/apps/tiktok",
    ]:
        nav(ws, create_url, wait=5)
        url = cur_url(ws)
        print(f"  URL: {url}")
        if "tiktok" in url or "auth" in url or "create" in url or "new" in url:
            break

    ss(ws, "precise_6_create_auth.png")
    page_text = js_eval(ws, "document.body.innerText") or ""
    print(f"  Texto: {page_text[:400]}")

    # Buscar botón de Setup/Connect
    for btn_text in ["Setup Integration", "Connect", "Add", "Enable", "Authorize", "Get Started"]:
        result = click_element_by_text(ws, btn_text)
        if result:
            time.sleep(5)
            ss(ws, "precise_7_oauth.png")
            url = cur_url(ws)
            print(f"  URL post-click: {url[:100]}")
            if "tiktok.com" in url:
                print("\n✅ TikTok OAuth abierto en Chrome!")
                # Auto-authorize si está logueado
                time.sleep(3)
                for auth_text in ["Authorize", "Allow", "Confirm", "Log in"]:
                    auth = click_element_by_text(ws, auth_text)
                    if auth:
                        print(f"  Auto-click: {auth_text}")
                        time.sleep(5)
                        ss(ws, "precise_8_authorized.png")
                        final_url = cur_url(ws)
                        if "composio" in final_url:
                            print("\n✅ OAuth TikTok COMPLETADO!")
                        break
            break

    ws.close()
    print("\n[DONE] Ver screenshots precise_*.png")


if __name__ == "__main__":
    main()
