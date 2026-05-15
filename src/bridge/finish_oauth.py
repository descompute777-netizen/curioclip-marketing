"""
Finaliza el setup de Composio y Pexels basado en el estado actual de las páginas.
python -m src.bridge.finish_oauth
"""
import sys, json, time, urllib.request, base64
sys.stdout.reconfigure(encoding='utf-8')
import websocket

CDP_URL = "http://localhost:9222"
_ID = [0]

def _id():
    _ID[0] += 1
    return _ID[0]

def get_tabs():
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    return [t for t in tabs if t.get("type") == "page"]

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
    for _ in range(100):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid:
                return r
        except Exception:
            return None
    return None

def nav(ws, url, wait=5):
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(wait)

def js(ws, code, await_p=False):
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

def cur_url(ws):
    return js(ws, "window.location.href") or ""

def click_text(ws, text):
    """Click el primer elemento que contenga el texto dado."""
    code = f"""
    (function() {{
        const all = [...document.querySelectorAll('button, a, [role=button], input[type=submit]')];
        const el = all.find(e => e.textContent.trim().includes({json.dumps(text)}));
        if (el) {{ el.click(); return el.textContent.trim(); }}
        return null;
    }})()
    """
    result = js(ws, code)
    return result

def click_selector(ws, selector):
    code = f"""
    (function() {{
        const el = document.querySelector({json.dumps(selector)});
        if (el) {{ el.click(); return el.textContent.trim() || el.value || 'clicked'; }}
        return null;
    }})()
    """
    return js(ws, code)

def get_page_text(ws):
    return js(ws, "document.body.innerText") or ""


# ─── PEXELS ──────────────────────────────────────────────────────────────────

def handle_pexels():
    print("\n" + "="*60)
    print("PEXELS API KEY")
    print("="*60)

    tab = open_tab()
    ws = ws_connect(tab["webSocketDebuggerUrl"])

    # Navegar a la API page
    print("[NAV] pexels.com/api/...")
    nav(ws, "https://www.pexels.com/api/", wait=4)
    ss(ws, "pexels_1_initial.png")
    url = cur_url(ws)
    print(f"  URL: {url}")

    # Modal: "What are you mainly using Pexels for?"
    # Click "Download content"
    print("[CLICK] 'Download content' en el modal...")
    result = click_text(ws, "Download content")
    if not result:
        result = click_selector(ws, "button:first-of-type")
    print(f"  Click: {result}")
    time.sleep(2)
    ss(ws, "pexels_2_after_modal.png")

    # Ahora debería aparecer el formulario de registro o redirigir a login
    # Buscar Get Started / Join
    result = click_text(ws, "Get Started")
    if not result:
        result = click_text(ws, "Join")
    if not result:
        result = click_selector(ws, ".get-started-btn, [href*='join'], [href*='signup']")
    print(f"  Get Started click: {result}")
    time.sleep(3)
    ss(ws, "pexels_3_register.png")
    url = cur_url(ws)
    print(f"  URL: {url}")

    # Página de registro/login — buscar "Continue with Google"
    if "join" in url or "login" in url or "signup" in url or "register" in url or "pexels" in url:
        print("[LOGIN] Buscando 'Continue with Google'...")
        # Esperar que cargue
        time.sleep(2)

        # Intentar diferentes variantes del botón Google
        for text in ["Continue with Google", "Google", "Sign in with Google", "Sign up with Google"]:
            result = click_text(ws, text)
            if result:
                print(f"  Found: {result}")
                break

        if not result:
            # Buscar por href o data-provider
            result = click_selector(ws,
                "[href*='google'], [data-provider='google'], "
                "button[aria-label*='Google'], .google-btn")
            print(f"  Google selector: {result}")

        time.sleep(5)
        ss(ws, "pexels_4_google_auth.png")
        url = cur_url(ws)
        print(f"  URL post-Google: {url}")

        # Si llegamos a accounts.google.com, el usuario ya está logueado
        if "accounts.google.com" in url:
            # Seleccionar la cuenta de gmail
            time.sleep(3)
            page_text = get_page_text(ws)
            if "descompute777" in page_text or "gmail" in page_text.lower():
                result = click_text(ws, "descompute777")
                if not result:
                    result = js(ws, """
                    (function(){
                        const divs = document.querySelectorAll('[data-identifier], .jR3Rfb, .GBg5jf');
                        if (divs[0]) { divs[0].click(); return 'account clicked'; }
                        return null;
                    })()
                    """)
                print(f"  Account select: {result}")
                time.sleep(5)
                ss(ws, "pexels_5_google_selected.png")

    # Buscar API key en la página actual
    time.sleep(3)
    nav(ws, "https://www.pexels.com/api/", wait=4)
    ss(ws, "pexels_6_api_page.png")
    url = cur_url(ws)
    print(f"  Final API page URL: {url}")

    # Buscar la API key
    api_key = js(ws, """
    (function() {
        // Buscar en inputs
        for (const inp of document.querySelectorAll('input')) {
            const v = inp.value || '';
            if (v.length >= 32 && v.length <= 100 && /^[A-Za-z0-9]+$/.test(v)) return v;
        }
        // Buscar en code/pre
        for (const el of document.querySelectorAll('code, pre, .api-key, [class*="key"]')) {
            const t = el.textContent.trim();
            if (t.length >= 32 && t.length <= 100 && /^[A-Za-z0-9]+$/.test(t)) return t;
        }
        // Buscar en el texto completo
        const match = document.body.innerText.match(/Your API key[:\s]+([A-Za-z0-9]{32,})/i);
        if (match) return match[1];
        return null;
    })()
    """)

    if api_key and len(str(api_key)) >= 32:
        print(f"\n✅ PEXELS API KEY: {api_key}")
        save_pexels_key(api_key)
        ws.close()
        return api_key
    else:
        page_text = get_page_text(ws)
        print(f"\n⚠️  No se encontró la API key automáticamente.")
        print(f"   Texto en página (primeros 300 chars): {page_text[:300]}")
        print(f"\n📋 Abre tu Chrome y ve a pexels.com/api/")
        print(f"   Si ya estás logueado, la API key aparece ahí directamente.")
        print(f"   Cópiala y agrégala al .env: PEXELS_API_KEY=tu_key")

    ws.close()
    return None


def save_pexels_key(key):
    import pathlib
    env = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
    content = env.read_text(encoding="utf-8")
    if "PEXELS_API_KEY" not in content:
        env.write_text(content + f"\nPEXELS_API_KEY={key}\n", encoding="utf-8")
        print("  ✅ Guardada en .env")
    else:
        # Actualizar
        import re
        new_content = re.sub(r'PEXELS_API_KEY=.*', f'PEXELS_API_KEY={key}', content)
        env.write_text(new_content, encoding="utf-8")
        print("  ✅ Actualizada en .env")


# ─── COMPOSIO ────────────────────────────────────────────────────────────────

def handle_composio():
    print("\n" + "="*60)
    print("COMPOSIO TIKTOK OAUTH")
    print("="*60)

    tab = open_tab()
    ws = ws_connect(tab["webSocketDebuggerUrl"])

    # Navegar al dashboard de Composio (usuario ya autenticado)
    print("[NAV] Composio connected accounts...")
    # Probar diferentes URLs del dashboard
    composio_urls = [
        "https://app.composio.dev/connected_accounts",
        "https://platform.composio.dev/connected-accounts",
        "https://dashboard.composio.dev/connected_accounts",
    ]

    for url in composio_urls:
        nav(ws, url, wait=6)
        current = cur_url(ws)
        if "composio" in current and "login" not in current:
            break
        time.sleep(2)

    ss(ws, "composio_dashboard.png")
    current = cur_url(ws)
    print(f"  URL: {current}")

    # Buscar TikTok en la lista de apps o connected accounts
    page_text = get_page_text(ws)
    if "TikTok" in page_text or "tiktok" in page_text.lower():
        print("  TikTok encontrado en la página")

        # Si ya está conectado
        if "connected" in page_text.lower() or "active" in page_text.lower():
            print("  ✅ TikTok ya puede estar conectado")
            ss(ws, "composio_tiktok_status.png")
        else:
            # Hacer click en Connect/Add TikTok
            result = click_text(ws, "Connect TikTok")
            if not result:
                result = click_text(ws, "Add TikTok")
            if not result:
                result = click_text(ws, "Connect")
            print(f"  Click Connect: {result}")
            time.sleep(5)
            ss(ws, "composio_tiktok_oauth.png")
            url_after = cur_url(ws)
            print(f"  URL post-click: {url_after}")
    else:
        # Navegar a la página de la app TikTok
        print("  TikTok no visible. Buscando en apps...")
        nav(ws, "https://app.composio.dev/apps", wait=6)
        ss(ws, "composio_apps.png")

        # Buscar TikTok en la lista
        result = js(ws, """
        (function() {
            const all = [...document.querySelectorAll('a, button, [role=button]')];
            const tiktok = all.find(e =>
                e.textContent.toLowerCase().includes('tiktok') ||
                (e.href || '').toLowerCase().includes('tiktok')
            );
            if (tiktok) { tiktok.click(); return tiktok.textContent.trim() || tiktok.href; }
            return null;
        })()
        """)
        print(f"  TikTok found+click: {result}")
        time.sleep(5)
        ss(ws, "composio_tiktok_app.png")
        current = cur_url(ws)
        print(f"  URL: {current}")

        # Hacer click en Connect
        time.sleep(2)
        result = click_text(ws, "Connect")
        if not result:
            result = click_text(ws, "Add")
        print(f"  Connect click: {result}")
        time.sleep=5
        ss(ws, "composio_oauth_start.png")
        url_after = cur_url(ws)
        print(f"  URL final: {url_after}")

        # Si llegamos a TikTok OAuth, el proceso está en marcha
        if "tiktok.com" in url_after:
            print("\n  📱 TikTok OAuth iniciado en Chrome.")
            print("  Si ya estás logueado en TikTok, puede completarse automáticamente.")
            print("  Mira tu Chrome para ver si hay un botón 'Authorize'.")

    ws.close()


def main():
    # Verificar Chrome
    try:
        with urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=3) as r:
            d = json.loads(r.read())
            print(f"✅ Chrome: {d.get('Browser','?')}")
    except Exception as e:
        print(f"❌ Chrome no disponible: {e}")
        return

    handle_composio()
    handle_pexels()

    print("\n" + "="*60)
    print("PROCESO COMPLETADO")
    print("Revisa los screenshots para ver el estado de cada OAuth.")
    print("="*60)


if __name__ == "__main__":
    main()
