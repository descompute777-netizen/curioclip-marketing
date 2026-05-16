"""
Usa el Auth Config ac_zehMCGYPXa3C para conectar TikTok en Composio.
Obtiene el redirectUrl de OAuth y lo abre en Chrome para autorización.
"""
import sys, json, time, urllib.request, base64, websocket, pathlib
sys.stdout.reconfigure(encoding='utf-8')

COMPOSIO_KEY = "ck_NcIb61zkczdt9WOrGTYQ"
AUTH_CONFIG_ID = "ac_zehMCGYPXa3C"
CDP = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")

import cloudscraper
s = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows"})

def try_api(method, url, body=None):
    headers = {"x-api-key": COMPOSIO_KEY, "Content-Type": "application/json"}
    try:
        if method == "GET":
            r = s.get(url, headers=headers, timeout=15)
        else:
            r = s.post(url, headers=headers, json=body, timeout=15)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)

def open_in_chrome(url):
    """Abre una URL en Chrome via CDP."""
    _ID = [0]
    def _id(): _ID[0] += 1; return _ID[0]
    with urllib.request.urlopen(f"{CDP}/json/new", ) as r:
        pass
    req = urllib.request.Request(f"{CDP}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        tab = json.loads(r.read())
    ws = websocket.WebSocket()
    ws.connect(tab["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": "Page.navigate", "params": {"url": url}}))
    time.sleep(5)
    mid2 = _id()
    ws.send(json.dumps({"id": mid2, "method": "Runtime.evaluate",
                        "params": {"expression": "window.location.href", "returnByValue": True}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid2:
                current = r.get("result", {}).get("result", {}).get("value", "")
                print(f"  Chrome abierto en: {current[:100]}")
                break
        except: break
    # Screenshot
    mid3 = _id()
    ws.send(json.dumps({"id": mid3, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid3:
                data = r.get("result", {}).get("data", "")
                if data:
                    with open("tiktok_oauth_screen.png", "wb") as f:
                        f.write(base64.b64decode(data))
                    print("  Screenshot: tiktok_oauth_screen.png")
                break
        except: break
    ws.close()


print("=" * 60)
print("CONECTAR TIKTOK VIA COMPOSIO AUTH CONFIG")
print(f"Auth Config ID: {AUTH_CONFIG_ID}")
print("=" * 60)

BASE = "https://backend.composio.dev"

# 1. Verificar el auth config
print("\n[1] Verificando Auth Config...")
endpoints_to_try = [
    f"{BASE}/api/v3/auth_configs/{AUTH_CONFIG_ID}",
    f"{BASE}/api/v1/auth_configs/{AUTH_CONFIG_ID}",
    f"{BASE}/api/v3/integrations/{AUTH_CONFIG_ID}",
]
for ep in endpoints_to_try:
    code, text = try_api("GET", ep)
    print(f"  [{code}] {ep.split('dev')[1]}: {text[:200]}")
    if code == 200:
        print("  *** Auth Config encontrado! ***")
        break

# 2. Crear Connected Account usando el Auth Config ID
print("\n[2] Iniciando OAuth (createConnectedAccount)...")
payloads_to_try = [
    {"authConfigId": AUTH_CONFIG_ID, "entityId": "default"},
    {"integrationId": AUTH_CONFIG_ID, "entityId": "default", "data": {}},
    {"authConfigId": AUTH_CONFIG_ID, "userUuid": "default"},
]
endpoints_post = [
    f"{BASE}/api/v3/connectedAccounts",
    f"{BASE}/api/v1/connectedAccounts",
]
redirect_url = None
for ep in endpoints_post:
    for payload in payloads_to_try:
        code, text = try_api("POST", ep, payload)
        print(f"  [{code}] {ep.split('dev')[1]} payload={list(payload.keys())}: {text[:250]}")
        if code in (200, 201):
            try:
                data = json.loads(text)
                redirect_url = data.get("redirectUrl") or data.get("redirect_url")
                if redirect_url:
                    print(f"\n  ✅ REDIRECT URL: {redirect_url}")
                    break
            except: pass
    if redirect_url:
        break

# 3. Abrir la URL de OAuth en Chrome
if redirect_url and redirect_url.startswith("http"):
    print(f"\n[3] Abriendo TikTok OAuth en Chrome...")
    open_in_chrome(redirect_url)
    print("\n  ✅ Página de OAuth de TikTok abierta.")
    print("  Si ya estás logueado en TikTok, el OAuth se completa automáticamente.")
    print("  Ver tiktok_oauth_screen.png para el estado actual.")
else:
    print("\n[3] No se obtuvo redirectUrl vía API.")
    print("\n  OPCIÓN ALTERNATIVA: El usuario puede conectar manualmente en Composio:")
    print("  1. Ve a dashboard.composio.dev → Users → sarah_user")
    print("  2. Click en 'Add connection' → TikTok")
    print(f"  3. Seleccionar Auth Config: {AUTH_CONFIG_ID}")
    print("  4. Completar OAuth de TikTok")
    print("\n  O usa la CLI de Composio:")
    print(f"  composio add tiktok --auth-config {AUTH_CONFIG_ID}")
