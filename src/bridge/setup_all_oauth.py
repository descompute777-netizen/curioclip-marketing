"""
Configura todos los OAuth necesarios navegando Chrome via CDP.
1. Composio → TikTok OAuth
2. Pexels → API key

python -m src.bridge.setup_all_oauth
"""
import sys, json, time, urllib.request, base64, subprocess
sys.stdout.reconfigure(encoding='utf-8')
import websocket

CDP_URL = "http://localhost:9222"
COMPOSIO_KEY = "ck_NcIb61zkczdt9WOrGTYQ"
USER_EMAIL = "descompute777@gmail.com"
_ID = [0]

def _id():
    _ID[0] += 1
    return _ID[0]

def open_tab():
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())

def ws_connect(ws_url):
    ws = websocket.WebSocket()
    ws.connect(ws_url, timeout=10, origin="http://localhost:9222")
    return ws

def cdp(ws, method, params=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    for _ in range(50):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid:
                return r
        except Exception:
            return None
    return None

def nav(ws, url):
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(4)

def cur_url(ws):
    r = cdp(ws, "Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value", "")

def run_js(ws, code, await_promise=False):
    r = cdp(ws, "Runtime.evaluate", {
        "expression": code,
        "returnByValue": True,
        "awaitPromise": await_promise
    })
    return (r or {}).get("result", {}).get("result", {}).get("value")

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

# ─── COMPOSIO TikTok OAuth ────────────────────────────────────────────────────

def setup_composio_tiktok():
    print("\n" + "="*60)
    print("PASO 1: Composio TikTok OAuth")
    print("="*60)

    # 1a. Intentar obtener redirectUrl via cloudscraper (v3 API)
    redirect_url = None
    try:
        import cloudscraper
        s = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows"})

        # Buscar TikTok integration UUID
        print("[API] Buscando UUID de integración TikTok...")
        for endpoint in [
            "https://backend.composio.dev/api/v3/apps/tiktok",
            "https://backend.composio.dev/api/v1/apps/tiktok",
            "https://backend.composio.dev/api/v3/integrations?appName=tiktok",
        ]:
            r = s.get(endpoint, headers={"x-api-key": COMPOSIO_KEY}, timeout=10)
            print(f"  {endpoint.split('dev')[1]}: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                uuid = (data.get("integrationId") or data.get("id") or
                        (data.get("items", [{}])[0].get("id") if "items" in data else None))
                if uuid:
                    print(f"  UUID encontrado: {uuid}")
                    # Crear conexión
                    r2 = s.post(
                        "https://backend.composio.dev/api/v3/connectedAccounts",
                        headers={"x-api-key": COMPOSIO_KEY, "Content-Type": "application/json"},
                        json={"integrationId": uuid, "entityId": "default", "data": {}},
                        timeout=15
                    )
                    print(f"  Create connection: {r2.status_code}")
                    if r2.status_code in (200, 201):
                        resp_data = r2.json()
                        redirect_url = resp_data.get("redirectUrl") or resp_data.get("redirect_url")
                        if redirect_url:
                            print(f"  redirectUrl: {redirect_url[:80]}")
                        break

    except Exception as e:
        print(f"  cloudscraper: {e}")

    # 1b. Navegar a Composio directamente en Chrome
    tab = open_tab()
    ws = ws_connect(tab["webSocketDebuggerUrl"])

    if redirect_url and redirect_url.startswith("http"):
        print(f"\n[NAV] Abriendo TikTok OAuth URL en Chrome...")
        nav(ws, redirect_url)
        url = cur_url(ws)
        print(f"  URL: {url[:100]}")
        ss(ws, "composio_tiktok_oauth.png")

        if "tiktok.com" in url and ("login" not in url and "oauth" in url.lower()):
            print("  [AUTO] TikTok OAuth en progreso...")
            # Buscar botón de autorización
            time.sleep(3)
            authorize_js = """
            document.querySelector('button[type="submit"], button.oauth-btn,
                input[type="submit"], a.authorize-btn')?.click()
            """
            run_js(ws, authorize_js)
            time.sleep(3)
            final_url = cur_url(ws)
            ss(ws, "composio_tiktok_done.png")
            print(f"  URL final: {final_url[:100]}")
    else:
        # Navegar directamente a Composio para conectar TikTok
        print("[NAV] Navegando a app.composio.dev/apps/tiktok...")
        nav(ws, "https://app.composio.dev/apps/tiktok")
        url = cur_url(ws)
        ss(ws, "composio_app.png")
        print(f"  URL: {url[:100]}")

        if "composio.dev" in url:
            # Intentar hacer clic en botón Connect de TikTok
            time.sleep(2)
            connect_js = """
            (function() {
                const btns = [...document.querySelectorAll('button, a')];
                const connectBtn = btns.find(b =>
                    (b.textContent || '').toLowerCase().includes('connect') ||
                    (b.textContent || '').toLowerCase().includes('tiktok')
                );
                if (connectBtn) { connectBtn.click(); return connectBtn.textContent.trim(); }
                return 'no button found';
            })()
            """
            result = run_js(ws, connect_js)
            print(f"  Click result: {result}")
            time.sleep(4)
            url_after = cur_url(ws)
            ss(ws, "composio_after_click.png")
            print(f"  URL post-click: {url_after[:100]}")
        else:
            print("  No se pudo llegar a Composio. Ver composio_app.png")

    ws.close()
    print("\n[COMPOSIO DONE] Ver screenshots para estado del OAuth.")

# ─── Pexels API Key ──────────────────────────────────────────────────────────

def setup_pexels():
    print("\n" + "="*60)
    print("PASO 2: Pexels API Key")
    print("="*60)

    tab = open_tab()
    ws = ws_connect(tab["webSocketDebuggerUrl"])

    # Navegar a Pexels API page
    print("[NAV] Navegando a pexels.com/api/...")
    nav(ws, "https://www.pexels.com/api/")
    url = cur_url(ws)
    ss(ws, "pexels_api_page.png")
    print(f"  URL: {url[:80]}")

    # Verificar si ya tiene API key (si hay sesión)
    api_key = run_js(ws, """
    (function() {
        const inputs = document.querySelectorAll('input[type="text"], input[readonly], input.api-key-input');
        for (const inp of inputs) {
            if (inp.value && inp.value.length > 20) return inp.value;
        }
        const codes = document.querySelectorAll('code, .api-key, [data-key]');
        for (const c of codes) {
            if (c.textContent && c.textContent.length > 20) return c.textContent.trim();
        }
        return null;
    })()
    """)

    if api_key and len(str(api_key)) > 20:
        print(f"\n[KEY FOUND] Pexels API Key: {api_key}")
        save_pexels_key(api_key)
        ws.close()
        return api_key

    # No hay sesión - intentar registro/login con Google
    print("[LOGIN] No hay sesión activa. Intentando login con Google...")

    # Buscar botón de login
    login_js = """
    (function() {
        const btns = [...document.querySelectorAll('a, button')];
        const loginBtn = btns.find(b =>
            (b.textContent || '').toLowerCase().includes('sign up') ||
            (b.textContent || '').toLowerCase().includes('join') ||
            (b.textContent || '').toLowerCase().includes('log in') ||
            (b.href || '').includes('login')
        );
        if (loginBtn) { loginBtn.click(); return loginBtn.textContent.trim() || loginBtn.href; }
        return 'no login button';
    })()
    """
    result = run_js(ws, login_js)
    print(f"  Login click: {result}")
    time.sleep(4)
    url = cur_url(ws)
    ss(ws, "pexels_login.png")
    print(f"  URL post-login: {url[:80]}")

    # Buscar botón de Google OAuth
    google_js = """
    (function() {
        const btns = [...document.querySelectorAll('a, button')];
        const gBtn = btns.find(b =>
            (b.textContent || '').toLowerCase().includes('google') ||
            (b.href || '').includes('google') ||
            (b.href || '').includes('oauth')
        );
        if (gBtn) { gBtn.click(); return gBtn.textContent.trim() || gBtn.href; }
        return 'no google button';
    })()
    """
    time.sleep(2)
    g_result = run_js(ws, google_js)
    print(f"  Google OAuth click: {g_result}")
    time.sleep(5)
    url = cur_url(ws)
    ss(ws, "pexels_google_auth.png")
    print(f"  URL post-Google: {url[:80]}")

    # Navegar al dashboard de la API
    time.sleep(2)
    nav(ws, "https://www.pexels.com/api/")
    time.sleep(3)
    url = cur_url(ws)
    ss(ws, "pexels_dashboard.png")
    print(f"  Dashboard URL: {url[:80]}")

    # Volver a buscar la API key
    api_key = run_js(ws, """
    (function() {
        const inputs = document.querySelectorAll('input');
        for (const inp of inputs) {
            if ((inp.value || '').length > 20) return inp.value;
        }
        const codes = document.querySelectorAll('code, pre, .key, [class*="api"]');
        for (const c of codes) {
            const txt = c.textContent.trim();
            if (txt.length > 20 && txt.length < 200) return txt;
        }
        return document.body.innerText.match(/[A-Za-z0-9]{32,64}/)?.[0] || null;
    })()
    """)

    if api_key and len(str(api_key)) > 20:
        print(f"\n[KEY FOUND] Pexels API Key: {api_key}")
        save_pexels_key(api_key)
    else:
        print(f"\n[MANUAL] No se pudo obtener la key automáticamente.")
        print(f"  1. Ve a pexels.com/api en tu Chrome")
        print(f"  2. Registra con Google ({USER_EMAIL})")
        print(f"  3. Copia la API key que aparece")
        print(f"  4. Pégala en .env: PEXELS_API_KEY=TU_KEY")
        print(f"  5. Luego corre: python scripts/setup_github_secrets.py --token TU_PAT")

    ws.close()
    return api_key


def save_pexels_key(key):
    import pathlib
    env_path = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
    content = env_path.read_text(encoding="utf-8")
    if "PEXELS_API_KEY" not in content:
        content += f"\nPEXELS_API_KEY={key}\n"
        env_path.write_text(content, encoding="utf-8")
        print(f"  [OK] Guardada en .env")
    else:
        print(f"  [INFO] PEXELS_API_KEY ya existe en .env")


def main():
    print("="*60)
    print("SETUP COMPLETO — Composio TikTok + Pexels")
    print("="*60)

    # Verificar Chrome
    try:
        with urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=3) as r:
            d = json.loads(r.read())
            print(f"Chrome: {d.get('Browser', '?')} ✓")
    except Exception as e:
        print(f"Chrome no disponible: {e}")
        print("Ejecuta primero: python -m src.bridge.chrome_bridge launch")
        return

    setup_composio_tiktok()
    setup_pexels()

    print("\n" + "="*60)
    print("SETUP COMPLETADO")
    print("Ver screenshots: composio_app.png, pexels_dashboard.png")
    print("="*60)


if __name__ == "__main__":
    main()
