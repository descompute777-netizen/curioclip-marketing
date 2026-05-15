"""
Registra en Pexels y obtiene API key via Chrome Bridge.
python -m src.bridge.pexels_register
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def open_tab():
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())["webSocketDebuggerUrl"]

def ws_connect(ws_url):
    ws = websocket.WebSocket()
    ws.connect(ws_url, timeout=10, origin="http://localhost:9222")
    return ws

def cdp(ws, method, params=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
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

def nav(ws, url, wait=5):
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(wait)

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

def click_by_text(ws, *texts):
    for text in texts:
        code = f"""
        (function() {{
            const all = [...document.querySelectorAll('button, a, [role=button], input[type=submit]')];
            const el = all.find(e => e.textContent.trim().includes({json.dumps(text)}));
            if (el) {{
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {{
                    return JSON.stringify({{text: el.textContent.trim().slice(0,30), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)}});
                }}
            }}
            return null;
        }})()
        """
        result = js(ws, code)
        if result:
            try:
                data = json.loads(result)
                print(f"  Click '{data['text']}' at ({data['x']},{data['y']})")
                click(ws, data['x'], data['y'])
                return data
            except: pass
    return None

def find_api_key(ws):
    return js(ws, """
    (function() {
        // Buscar en inputs
        for (const inp of document.querySelectorAll('input, textarea')) {
            const v = (inp.value || '').trim();
            if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return v;
        }
        // Buscar en el texto de la página
        const body = document.body.innerText;
        const m = body.match(/[A-Za-z0-9]{32,64}/g);
        if (m) {
            // Filtrar tokens que no sean URLs ni hashes de git
            return m.find(t => t.length >= 32 && t.length <= 64 && !/[=+\/]/.test(t)) || null;
        }
        return null;
    })()
    """)

def main():
    print("="*50)
    print("PEXELS API KEY REGISTRATION")
    print("="*50)

    ws_url = open_tab()
    ws = ws_connect(ws_url)

    # Navegar a la página API de Pexels
    print("\n[1] Navegando a pexels.com/api/...")
    nav(ws, "https://www.pexels.com/api/", wait=5)
    ss(ws, "pex1_api.png")

    # Verificar si ya tiene API key (cuenta existente)
    key = find_api_key(ws)
    if key:
        print(f"\n✅ API Key encontrada: {key}")
        save_key(key)
        ws.close()
        return

    # Hacer click en "Get Started" para ir al registro
    print("\n[2] Buscando botón Get Started...")
    result = click_by_text(ws, "Get Started", "Get started", "get started")
    if not result:
        # Navegar directamente a registro
        nav(ws, "https://www.pexels.com/join/", wait=5)
    time.sleep(3)
    ss(ws, "pex2_register.png")
    print(f"  URL: {js(ws, 'window.location.href')}")

    # Hacer click en "Continue with Google"
    print("\n[3] Buscando Google OAuth...")
    result = click_by_text(ws, "Continue with Google", "Sign up with Google", "Google", "Sign in with Google")
    if result:
        time.sleep(6)
        ss(ws, "pex3_google.png")
        url = js(ws, "window.location.href")
        print(f"  URL: {url}")

        # Si estamos en accounts.google.com, seleccionar la cuenta
        if "accounts.google.com" in str(url):
            print("\n[4] Seleccionando cuenta Google...")
            time.sleep(2)
            # Buscar el email del usuario
            email_result = click_by_text(ws, "descompute777", "descompute777@gmail.com")
            if not email_result:
                # Hacer click en la primera cuenta disponible
                account_click = js(ws, """
                (function() {
                    const accounts = document.querySelectorAll('[data-email], .jR3Rfb, [data-identifier]');
                    if (accounts[0]) {
                        accounts[0].click();
                        return 'clicked first account';
                    }
                    const divs = document.querySelectorAll('div[role=link]');
                    if (divs[0]) { divs[0].click(); return 'clicked div link'; }
                    return null;
                })()
                """)
                print(f"  Account click: {account_click}")
            time.sleep(5)
            ss(ws, "pex4_google_auth.png")
            url = js(ws, "window.location.href")
            print(f"  URL post-account: {url}")

    # Volver a la página de API
    print("\n[5] Verificando API key...")
    time.sleep(3)
    nav(ws, "https://www.pexels.com/api/", wait=5)
    ss(ws, "pex5_api_check.png")

    key = find_api_key(ws)
    if key:
        print(f"\n✅ API Key: {key}")
        save_key(key)
    else:
        url = js(ws, "window.location.href")
        print(f"\n⚠️  Key no encontrada automáticamente.")
        print(f"   URL actual: {url}")
        print(f"   Abre tu Chrome y ve a pexels.com/api/")
        print(f"   Si estás logueado, la key aparece directamente en la página.")
        print(f"   Cópiala y corre:")
        print(f"   python -c \"")
        print(f"   import pathlib")
        print(f"   p = pathlib.Path(r'C:/Users/Nick/Desktop/AGENCIA DE MARKETING/.env')")
        print(f"   p.write_text(p.read_text() + 'PEXELS_API_KEY=TU_KEY\\n')\"")

    ws.close()


def save_key(key):
    import pathlib, re
    env = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
    content = env.read_text(encoding="utf-8")
    if "PEXELS_API_KEY" in content:
        content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
    else:
        content += f"\nPEXELS_API_KEY={key}\n"
    env.write_text(content, encoding="utf-8")
    print("  ✅ Guardada en .env")


if __name__ == "__main__":
    main()
