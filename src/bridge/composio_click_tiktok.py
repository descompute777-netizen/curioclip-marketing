"""
Navega Composio usando clics por coordenadas (compatible con SPA React).
1. Click en "Auth Configs" en el sidebar
2. Busca TikTok o botón de Add
3. Completa el OAuth

python -m src.bridge.composio_click_tiktok
"""
import sys, json, time, urllib.request, base64
sys.stdout.reconfigure(encoding='utf-8')
import websocket

CDP_URL = "http://localhost:9222"
_ID = [0]

def _id():
    _ID[0] += 1
    return _ID[0]

def get_composio_tab():
    """Encuentra la pestaña de Composio o abre una nueva."""
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    pages = [t for t in tabs if t.get("type") == "page"]

    # Buscar pestaña de Composio
    for t in pages:
        if "composio" in t.get("url", "").lower():
            return t["webSocketDebuggerUrl"]

    # Abrir nueva
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        tab = json.loads(r.read())
    return tab["webSocketDebuggerUrl"]

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

def click_at(ws, x, y):
    """Clic real via CDP Input events (funciona con React/SPAs)."""
    cdp(ws, "Input.dispatchMouseEvent", {
        "type": "mousePressed", "x": x, "y": y,
        "button": "left", "clickCount": 1
    })
    time.sleep(0.1)
    cdp(ws, "Input.dispatchMouseEvent", {
        "type": "mouseReleased", "x": x, "y": y,
        "button": "left", "clickCount": 1
    })

def nav(ws, url, wait=6):
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(wait)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"  📸 {path}")

def cur_url(ws):
    r = cdp(ws, "Runtime.evaluate", {
        "expression": "window.location.href",
        "returnByValue": True
    })
    return (r or {}).get("result", {}).get("result", {}).get("value", "")

def js(ws, code, await_p=False):
    r = cdp(ws, "Runtime.evaluate", {
        "expression": code, "returnByValue": True, "awaitPromise": await_p
    })
    return (r or {}).get("result", {}).get("result", {}).get("value")


def main():
    print("="*60)
    print("COMPOSIO TIKTOK OAUTH — Click Method")
    print("="*60)

    ws_url = get_composio_tab()
    ws = ws_connect(ws_url)

    # Navegar al dashboard
    print("[NAV] Composio dashboard...")
    nav(ws, "https://dashboard.composio.dev", wait=6)
    ss(ws, "c1_dashboard.png")
    print(f"  URL: {cur_url(ws)}")

    # Click en "Auth Configs" en el sidebar (coordenada ~x=95, y=487)
    print("[CLICK] Auth Configs...")
    click_at(ws, 95, 487)
    time.sleep(4)
    ss(ws, "c2_auth_configs.png")
    print(f"  URL: {cur_url(ws)}")

    # Si no funcionó, probar "Toolkits"
    url = cur_url(ws)
    if "auth" not in url and "toolkit" not in url:
        print("[CLICK] Toolkits (fallback y=320)...")
        click_at(ws, 80, 320)
        time.sleep(3)
        ss(ws, "c3_toolkits.png")
        print(f"  URL: {cur_url(ws)}")

    # Buscar TikTok en el contenido
    page_text = js(ws, "document.body.innerText") or ""
    tiktok_visible = "tiktok" in page_text.lower() or "TikTok" in page_text

    if not tiktok_visible:
        print("[SEARCH] Navegando directamente a TikTok en Composio...")
        nav(ws, "https://dashboard.composio.dev/apps/tiktok", wait=5)
        ss(ws, "c4_tiktok_app.png")
        print(f"  URL: {cur_url(ws)}")

    # Buscar botón "Setup Integration" / "Connect" / "Add"
    page_text = js(ws, "document.body.innerText") or ""
    print(f"  Página visible: {page_text[:200]}")

    # Buscar coordenadas del botón Connect/Setup usando el texto de la página
    setup_btn = js(ws, """
    (function() {
        const keywords = ['Setup Integration', 'Connect', 'Add TikTok', 'Enable', 'Authorize'];
        const all = [...document.querySelectorAll('button, a, [role=button]')];
        for (const kw of keywords) {
            const btn = all.find(e => e.textContent.trim().includes(kw));
            if (btn) {
                const rect = btn.getBoundingClientRect();
                return JSON.stringify({
                    text: btn.textContent.trim(),
                    x: Math.round(rect.left + rect.width/2),
                    y: Math.round(rect.top + rect.height/2)
                });
            }
        }
        return null;
    })()
    """)

    if setup_btn:
        try:
            btn_data = json.loads(setup_btn)
            print(f"  Botón encontrado: '{btn_data['text']}' en ({btn_data['x']}, {btn_data['y']})")
            click_at(ws, btn_data['x'], btn_data['y'])
            time.sleep(6)
            ss(ws, "c5_after_connect.png")
            url_after = cur_url(ws)
            print(f"  URL post-click: {url_after[:100]}")

            if "tiktok.com" in url_after:
                print("\n✅ TikTok OAuth iniciado!")
                print("  La página de TikTok está abierta en Chrome.")
                print("  Si ya estás logueado en TikTok, haz click en 'Authorize'.")

                # Buscar botón authorize en la página de TikTok
                time.sleep(3)
                auth_btn = js(ws, """
                (function() {
                    const btns = [...document.querySelectorAll('button, [role=button]')];
                    const auth = btns.find(b =>
                        b.textContent.toLowerCase().includes('authorize') ||
                        b.textContent.toLowerCase().includes('allow') ||
                        b.textContent.toLowerCase().includes('confirm')
                    );
                    if (auth) {
                        const r = auth.getBoundingClientRect();
                        return JSON.stringify({text: auth.textContent.trim(),
                            x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
                    }
                    return null;
                })()
                """)

                if auth_btn:
                    auth_data = json.loads(auth_btn)
                    print(f"  Auto-click en '{auth_data['text']}'")
                    click_at(ws, auth_data['x'], auth_data['y'])
                    time.sleep(5)
                    ss(ws, "c6_tiktok_auth.png")
                    final_url = cur_url(ws)
                    print(f"  URL final: {final_url[:100]}")
                    if "composio" in final_url:
                        print("\n✅ ¡OAuth de TikTok COMPLETADO!")
        except json.JSONDecodeError:
            print(f"  Botón data: {setup_btn}")
    else:
        print("  No se encontró botón de Connect.")
        ss(ws, "c5_no_button.png")
        page_text = js(ws, "document.body.innerText") or ""
        print(f"  Texto visible: {page_text[:400]}")

    ws.close()
    print("\n[DONE] Ver screenshots c*.png para el estado del OAuth.")


if __name__ == "__main__":
    main()
