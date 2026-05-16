"""
Encuentra la pestaña de TikTok OAuth y completa la autorización.
python -m src.bridge.find_oauth_tab
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_all_tabs():
    with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
        return json.loads(r.read())

def connect_tab(ws_url):
    ws = websocket.WebSocket()
    ws.connect(ws_url, timeout=10, origin="http://localhost:9222")
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

FIND_AUTHORIZE_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button, [role='button'], a, input[type='submit']"));
    var keywords = ["authorize", "allow", "confirm", "accept", "log in", "login", "continue", "next"];
    var found = [];
    btns.forEach(function(b) {
        var text = b.textContent.trim().toLowerCase();
        if (keywords.some(function(k) { return text.includes(k); }) && b.getBoundingClientRect().height > 0) {
            var r = b.getBoundingClientRect();
            found.push({text: b.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
        }
    });
    return JSON.stringify(found.slice(0, 5));
})()
"""


def main():
    print("=" * 60)
    print("FINDING TIKTOK OAUTH TAB")
    print("=" * 60)

    tabs = get_all_tabs()
    pages = [t for t in tabs if t.get("type") == "page"]

    print(f"\nTotal pestañas: {len(pages)}")
    print("\nPrimeras 15 URLs:")
    for t in pages[:15]:
        url = t.get("url", "")
        print(f"  {url[:100]}")

    # Buscar tab de TikTok OAuth (no Studio, no Analytics)
    oauth_tab = None
    exclusions = ["studio", "analytics", "tiktokstudio", "creator_center"]

    # Primero buscar URLs que claramente son OAuth
    for t in pages:
        url = t.get("url", "")
        if "tiktok.com" in url and any(kw in url.lower() for kw in ["oauth", "auth", "login", "open.tiktok"]):
            if not any(ex in url.lower() for ex in exclusions):
                oauth_tab = t
                print(f"\n✅ OAuth tab encontrada: {url[:120]}")
                break

    # Si no encontramos una clara, buscar tabs recientes de TikTok que no sean Studio
    if not oauth_tab:
        for t in pages:
            url = t.get("url", "")
            if "tiktok.com" in url and not any(ex in url.lower() for ex in exclusions):
                oauth_tab = t
                print(f"\n  Posible OAuth tab: {url[:120]}")
                break

    if not oauth_tab:
        print("\nNo se encontró tab de TikTok OAuth.")
        print("Composio pudo haber abierto la OAuth en la misma tab o falló.")
        return

    # Conectar a la tab y ver qué hay
    ws = connect_tab(oauth_tab["webSocketDebuggerUrl"])
    cdp(ws, "Page.bringToFront", {})
    time.sleep(2)

    ss(ws, "oauth_tab_found.png")
    current_url = js(ws, "window.location.href")
    page_text = js(ws, "document.body.innerText") or ""
    print(f"\nURL: {current_url}")
    print(f"Texto: {page_text[:400]}")

    # Buscar botones de autorización
    btns_raw = js(ws, FIND_AUTHORIZE_JS)
    btns = json.loads(btns_raw) if btns_raw else []
    print(f"\nBotones encontrados: {[b['text'] for b in btns]}")

    if btns:
        # Click en el más relevante
        best_btn = btns[0]
        for b in btns:
            if "authorize" in b["text"].lower() or "allow" in b["text"].lower():
                best_btn = b
                break
        print(f"\nClick en '{best_btn['text']}' ({best_btn['x']},{best_btn['y']})")
        click(ws, best_btn["x"], best_btn["y"])
        time.sleep(8)
        ss(ws, "oauth_after_auth.png")
        final_url = js(ws, "window.location.href")
        final_page = js(ws, "document.body.innerText") or ""
        print(f"\nURL post-auth: {final_url}")
        print(f"Texto: {final_page[:400]}")

        if "composio" in final_url or "success" in final_page.lower() or "connected" in final_page.lower():
            print("\n✅ TikTok OAuth COMPLETADO!")
        else:
            print("\n  OAuth no completado. Ver oauth_after_auth.png")
    else:
        print("\nNo se encontraron botones de autorización.")
        print("Puede que TikTok necesite login primero o ya está autorizado.")
        print("Ver oauth_tab_found.png")

    ws.close()


if __name__ == "__main__":
    main()
