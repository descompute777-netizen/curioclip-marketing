"""
Click en '+ Connect Account' en Composio para iniciar OAuth de TikTok.
python -m src.bridge.composio_connect_account
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def gws():
    with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "composio" in t.get("url", "").lower():
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

FIND_CONNECT_BTN_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button, a, [role='button']"));
    var b = btns.find(function(x) { return x.textContent.includes("Connect Account"); });
    if (b) {
        var r = b.getBoundingClientRect();
        return JSON.stringify({
            text: b.textContent.trim(),
            x: Math.round(r.left + r.width/2),
            y: Math.round(r.top + r.height/2)
        });
    }
    return null;
})()
"""

FIND_OAUTH_URL_JS = """
(function() {
    // Buscar si se abrió un iframe, link o redirect con OAuth
    var frames = document.querySelectorAll("iframe");
    for (var i=0; i<frames.length; i++) {
        if (frames[i].src && (frames[i].src.includes("tiktok") || frames[i].src.includes("oauth"))) {
            return "IFRAME:" + frames[i].src;
        }
    }
    // Buscar en links/buttons del modal
    var modal = document.querySelector("[role='dialog'], .modal, [data-modal]");
    if (modal) return "MODAL:" + modal.textContent.slice(0, 200);
    return "URL:" + window.location.href;
})()
"""


def main():
    print("=" * 60)
    print("COMPOSIO: CONNECT ACCOUNT → TIKTOK OAUTH")
    print("=" * 60)

    ws = gws()
    if not ws:
        print("No Composio tab found")
        return

    cdp(ws, "Page.bringToFront", {})
    time.sleep(0.5)

    # Tomar screenshot del estado actual
    ss(ws, "before_connect.png")
    current_url = js(ws, "window.location.href")
    print(f"\nURL actual: {current_url}")

    # Click en Connect Account
    print("\n[1] Buscando botón 'Connect Account'...")
    btn_raw = js(ws, FIND_CONNECT_BTN_JS)
    print(f"  Botón: {btn_raw}")

    if btn_raw:
        btn = json.loads(btn_raw)
        print(f"  Click en '{btn['text']}' ({btn['x']},{btn['y']})")
        click(ws, btn["x"], btn["y"])
    else:
        print("  No encontrado por texto, usando coordenada del center button (616, 455)")
        click(ws, 616, 455)

    # Esperar respuesta
    time.sleep(6)
    ss(ws, "after_connect_click.png")

    url_after = js(ws, "window.location.href")
    print(f"\n  URL post-click: {url_after}")

    # Ver si se abrió OAuth o algún modal
    oauth_info = js(ws, FIND_OAUTH_URL_JS)
    print(f"  OAuth info: {oauth_info}")

    page = js(ws, "document.body.innerText") or ""
    print(f"\n  Contenido visible:\n{page[:500]}")

    # Si llegamos a TikTok OAuth, el proceso está en marcha
    if "tiktok.com" in url_after.lower():
        print("\n✅ TikTok OAuth abierto directamente!")
        time.sleep(5)
        # Intentar click en Authorize si aparece
        authorize = js(ws, """
        (function() {
            var btns = Array.from(document.querySelectorAll("button, [role='button']"));
            var a = btns.find(function(b) {
                return b.textContent.toLowerCase().includes("authorize") ||
                       b.textContent.toLowerCase().includes("allow") ||
                       b.textContent.toLowerCase().includes("confirm");
            });
            if (a) { var r = a.getBoundingClientRect(); return JSON.stringify({text: a.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)}); }
            return null;
        })()
        """)
        if authorize:
            auth = json.loads(authorize)
            print(f"  Auto-click en '{auth['text']}'")
            click(ws, auth["x"], auth["y"])
            time.sleep(8)
            ss(ws, "tiktok_authorized.png")
            final_url = js(ws, "window.location.href")
            print(f"  URL final: {final_url}")
            if "composio" in final_url:
                print("\n✅ ¡OAuth de TikTok COMPLETADO!")
    elif "composio" in url_after and "connect" in url_after.lower():
        print("\n  Redirigido a página de conexión de Composio")
    else:
        print("\n  Estado después del click. Ver after_connect_click.png")

    ws.close()


if __name__ == "__main__":
    main()
