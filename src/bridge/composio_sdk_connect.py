"""
Conecta TikTok a Composio usando el Python SDK oficial.
Maneja versionado de API automáticamente.
python -m src.bridge.composio_sdk_connect
"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

COMPOSIO_KEY = "ck_NcIb61zkczdt9WOrGTYQ"
CDP_URL = "http://localhost:9222"


def get_tiktok_redirect_url():
    """Obtiene la URL de OAuth de TikTok desde Composio SDK."""
    from composio_openai import ComposioToolSet
    toolset = ComposioToolSet(api_key=COMPOSIO_KEY)

    # Verificar conexiones TikTok existentes
    print("[CHECK] Buscando conexiones TikTok existentes...")
    try:
        connections = toolset.client.connected_accounts.get()
        tiktok_conns = [c for c in connections.items
                        if 'tiktok' in str(getattr(c, 'appName', '')).lower()
                        or 'tiktok' in str(getattr(c, 'appUniqueId', '')).lower()]
        print(f"  Conexiones totales: {len(connections.items)}")
        print(f"  TikTok: {len(tiktok_conns)}")
        for c in tiktok_conns:
            status = getattr(c, 'status', '?')
            print(f"  - {getattr(c, 'id', '?')}: {status}")
            if status == 'ACTIVE':
                print("  [OK] TikTok ya conectado y activo!")
                return None  # Ya conectado
    except Exception as e:
        print(f"  Conexiones check error: {e}")

    # Iniciar nueva conexion
    print("\n[INIT] Iniciando OAuth TikTok...")
    try:
        entity = toolset.get_entity(id="default")

        # Intentar con App enum
        try:
            from composio import App
            request = entity.initiate_connection(app_name=App.TIKTOK)
        except (ImportError, AttributeError):
            # Fallback con string
            request = entity.initiate_connection(app_name="tiktok")

        redirect_url = getattr(request, 'redirectUrl', None) or \
                       getattr(request, 'redirect_url', None) or \
                       str(request)

        if redirect_url and redirect_url.startswith('http'):
            print(f"  redirect_url: {redirect_url}")
            return redirect_url
        else:
            print(f"  Response: {request}")
            return None

    except Exception as e:
        print(f"  initiate_connection error: {e}")
        import traceback
        traceback.print_exc()
        return None


def navigate_chrome_to_url(url):
    """Navega Chrome al URL usando CDP WebSocket con el origen correcto."""
    import urllib.request
    import websocket
    import time

    # Abrir nueva pestaña via CDP HTTP API
    print(f"\n[CDP] Abriendo nueva pestaña en Chrome...")
    try:
        req = urllib.request.Request(
            f"{CDP_URL}/json/new",
            method="PUT",
            data=b""
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            tab = json.loads(r.read())
        ws_url = tab["webSocketDebuggerUrl"]
        print(f"  Nueva pestaña: {tab.get('id', '?')}")
    except Exception as e:
        print(f"  Error abriendo pestaña: {e}")
        # Usar pestaña existente
        with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
            tabs = json.loads(r.read())
        pages = [t for t in tabs if t.get("type") == "page"]
        if not pages:
            print("  No hay pestañas disponibles")
            return False
        ws_url = pages[0]["webSocketDebuggerUrl"]
        print(f"  Usando pestaña existente")

    # Conectar WebSocket con el origen correcto
    try:
        ws = websocket.WebSocket()
        ws.connect(ws_url, timeout=10, origin="http://localhost:9222")
        print(f"  WebSocket conectado")
    except Exception as e:
        print(f"  Error WebSocket: {e}")
        return False

    # Navegar al URL
    import json as _json
    nav_msg = _json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}})
    ws.send(nav_msg)

    # Esperar respuesta
    attempts = 0
    while attempts < 10:
        try:
            resp = _json.loads(ws.recv())
            if resp.get("id") == 1:
                print(f"  Navegando a: {url[:80]}")
                break
        except Exception:
            pass
        attempts += 1

    time.sleep(4)

    # Capturar URL actual
    ws.send(_json.dumps({"id": 2, "method": "Runtime.evaluate",
                          "params": {"expression": "window.location.href",
                                     "returnByValue": True}}))
    attempts = 0
    while attempts < 10:
        try:
            resp = _json.loads(ws.recv())
            if resp.get("id") == 2:
                current_url = resp.get("result", {}).get("result", {}).get("value", "")
                print(f"  URL actual: {current_url[:100]}")
                break
        except Exception:
            pass
        attempts += 1

    # Screenshot
    ws.send(_json.dumps({"id": 3, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
    attempts = 0
    while attempts < 10:
        try:
            resp = _json.loads(ws.recv())
            if resp.get("id") == 3:
                import base64
                data = resp.get("result", {}).get("data", "")
                if data:
                    with open("oauth_progress.png", "wb") as f:
                        f.write(base64.b64decode(data))
                    print(f"  Screenshot: oauth_progress.png")
                break
        except Exception:
            pass
        attempts += 1

    ws.close()
    return True


def relaunch_chrome_with_flag():
    """Relanza Chrome con --remote-allow-origins=* si es necesario."""
    import subprocess, time

    print("[RELAUNCH] Relanzando Chrome con --remote-allow-origins=*...")

    # Matar Chrome actual (suavemente)
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"],
                   capture_output=True)
    time.sleep(2)

    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    PROFILE_DIR = str(Path.home() / "chrome-curioclip")
    from pathlib import Path

    subprocess.Popen([
        CHROME_PATH,
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank"
    ], shell=False)
    time.sleep(4)

    # Verificar
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:9222/json/version", timeout=3) as r:
            data = json.loads(r.read())
            print(f"  Chrome relanzado: {data.get('Browser', '?')}")
            return True
    except Exception as e:
        print(f"  Error verificando Chrome: {e}")
        return False


def main():
    from pathlib import Path

    print("="*60)
    print("COMPOSIO TIKTOK OAUTH — SDK Method")
    print("="*60)

    # 1. Obtener URL de OAuth
    redirect_url = get_tiktok_redirect_url()

    if not redirect_url:
        print("\n[INFO] TikTok ya conectado o no se pudo obtener URL.")
        return

    # 2. Verificar si Chrome acepta WebSocket con origen correcto
    print("\n[TEST] Verificando compatibilidad CDP WebSocket...")
    import urllib.request, websocket
    try:
        with urllib.request.urlopen(f"{CDP_URL}/json", timeout=3) as r:
            tabs = json.loads(r.read())
        if tabs:
            ws_url = tabs[0]["webSocketDebuggerUrl"]
            ws = websocket.WebSocket()
            ws.connect(ws_url, timeout=5, origin="http://localhost:9222")
            ws.close()
            print("  WebSocket OK con origin=http://localhost:9222")
            chrome_ok = True
    except Exception as e:
        print(f"  WebSocket falló: {e}")
        print("  Relanzando Chrome con --remote-allow-origins=*...")
        chrome_ok = relaunch_chrome_with_flag()

    # 3. Navegar a OAuth URL
    if chrome_ok or True:
        print(f"\n[OAUTH] Abriendo URL de TikTok OAuth en Chrome...")
        print(f"  URL: {redirect_url}")
        success = navigate_chrome_to_url(redirect_url)
        if success:
            print("\n[OK] Chrome navegó a la página de OAuth.")
            print("  Si TikTok ya está logueado, el OAuth puede completarse automáticamente.")
            print("  Verifica oauth_progress.png para ver el estado.")
        else:
            print(f"\n[MANUAL] Abre esta URL en tu Chrome:")
            print(f"  {redirect_url}")


if __name__ == "__main__":
    main()
