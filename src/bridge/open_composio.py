"""
Abre Composio Auth Configs en Chrome Bridge.
python -m src.bridge.open_composio
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
TARGET_URL = "https://dashboard.composio.dev/descompute777_workspace/descompute777_workspace_first_project/auth-configs"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_composio_tab_ws():
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    # Buscar tab de Composio existente
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "composio" in t.get("url", "").lower() or "dashboard" in t.get("url", "").lower():
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
            return ws, t["url"]
    # Abrir nueva pestaña
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        tab = json.loads(r.read())
    ws = websocket.WebSocket()
    ws.connect(tab["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
    return ws, "new"

def cdp(ws, m, p=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid: return r
        except: return None

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
    print("="*60)
    print("ABRIENDO COMPOSIO AUTH CONFIGS EN CHROME")
    print("="*60)

    ws, old_url = get_composio_tab_ws()
    print(f"\nTab anterior: {old_url[:80]}")

    # Navegar a Auth Configs
    print(f"\nNavegando a: {TARGET_URL}")
    cdp(ws, "Page.navigate", {"url": TARGET_URL})
    time.sleep(7)

    current = js(ws, "window.location.href")
    print(f"URL actual: {current}")

    # Screenshot para que el usuario vea
    ss(ws, "composio_auth_configs_ready.png")

    # Ver qué hay en pantalla
    page_text = js(ws, "document.body.innerText") or ""
    print(f"\nContenido visible:\n{page_text[:400]}")

    # Instrucciones precisas basadas en el estado
    if "Auth Config" in page_text or "auth" in current.lower():
        print("\n" + "="*60)
        print("✅ COMPOSIO AUTH CONFIGS ABIERTO EN TU CHROME")
        print("="*60)
        print("\nLo que ves en pantalla: la lista de Auth Configs.")
        print("Hay un botón '+ Create Auth Config' visible.")
        print("\nAcciones que necesitas hacer TÚ (3 clicks):")
        print("1. Click en '+ Create Auth Config'")
        print("2. En el modal que se abre: SCROLL hacia abajo hasta ver 'TikTok'")
        print("3. Click en TikTok → Click en 'Use Composio OAuth'")
        print("   → El OAuth de TikTok se abrirá (ya estás logueado)")
        print("\nSi TikTok no aparece al hacer scroll:")
        print("   Escribe 'tiktok' en el campo de búsqueda del modal")
        print("   (puede que el filtro funcione visualmente pero no en el DOM)")
    else:
        print("\nComposio no está mostrando Auth Configs.")
        print(f"URL actual: {current}")
        print("Intenta navegar manualmente a:")
        print(f"  {TARGET_URL}")

    ws.close()

if __name__ == "__main__":
    main()
