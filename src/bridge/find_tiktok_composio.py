"""
Encuentra TikTok en el modal de Composio y hace click.
python -m src.bridge.find_tiktok_composio
"""
import sys, json, time, urllib.request, base64, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_ws():
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "composio" in t.get("url", "").lower() or "dashboard" in t.get("url", "").lower():
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
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
    time.sleep(0.1)

def scroll(ws, x, y, dy):
    cdp(ws, "Input.dispatchMouseEvent", {"type": "mouseWheel", "x": x, "y": y, "deltaY": dy, "deltaX": 0})
    time.sleep(0.4)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True, "awaitPromise": False})
    return (r or {}).get("result", {}).get("result", {}).get("value")

def find_tiktok(ws):
    """Busca TikTok visible en pantalla y retorna sus coordenadas."""
    result = js(ws, """
    (function() {
        const candidates = [...document.querySelectorAll('*')];
        for (const el of candidates) {
            const t = el.textContent.trim();
            if (t.toLowerCase() === 'tiktok' && t.length < 15) {
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0 && r.top > 0 && r.top < window.innerHeight) {
                    return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
                }
            }
        }
        return null;
    })()
    """)
    return json.loads(result) if result else None

def trigger_react_search(ws, text):
    """Dispara la búsqueda en React correctamente."""
    code = """
    (function() {
        const inputs = [...document.querySelectorAll('input')];
        const searchInput = inputs.find(i =>
            (i.placeholder || '').toLowerCase().includes('search') ||
            (i.placeholder || '').toLowerCase().includes('toolkit')
        ) || inputs[0];

        if (!searchInput) return 'no input';

        searchInput.focus();
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(searchInput, '""" + text + """');

        ['input','change','keyup'].forEach(evt => {
            searchInput.dispatchEvent(new Event(evt, {bubbles: true, cancelable: true}));
        });
        return 'OK: ' + searchInput.value;
    })()
    """
    return js(ws, code)


def main():
    ws = get_ws()
    if not ws:
        print("No se encontró pestaña de Composio")
        return

    print("="*50)
    print("BUSCANDO TIKTOK EN COMPOSIO MODAL")
    print("="*50)

    # Intentar trigger React search
    print("\n[1] Disparando búsqueda React...")
    result = trigger_react_search(ws, "tiktok")
    print(f"    {result}")
    time.sleep(2)
    ss(ws, "search_react.png")

    # Buscar TikTok visible
    tiktok = find_tiktok(ws)
    if tiktok:
        print(f"\n[FOUND] TikTok en ({tiktok['x']}, {tiktok['y']})")
        click(ws, tiktok['x'], tiktok['y'])
        time.sleep(5)
        ss(ws, "tiktok_auth_config.png")
        url = js(ws, "window.location.href")
        print(f"  URL: {url}")
        page = js(ws, "document.body.innerText") or ""
        print(f"  Texto: {page[:200]}")

        # Si se abrió formulario de auth config, continuamos
        if "TikTok" in page or "tiktok" in page:
            # Buscar botón de Continue/Save/Submit
            submit = js(ws, """
            (function() {
                const btns = [...document.querySelectorAll('button')];
                const s = btns.find(b => ['Continue','Save','Next','Submit','Create','Use default','Use Composio']
                    .some(t => b.textContent.includes(t)));
                if (s) {
                    const r = s.getBoundingClientRect();
                    return JSON.stringify({text: s.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
                }
                return null;
            })()
            """)
            if submit:
                sdata = json.loads(submit)
                print(f"\n  Click '{sdata['text']}' en ({sdata['x']},{sdata['y']})")
                click(ws, sdata['x'], sdata['y'])
                time.sleep(4)
                ss(ws, "auth_config_submit.png")
                print("  Screenshot: auth_config_submit.png")
        return

    # Scroll para encontrar TikTok
    print("\n[2] TikTok no visible. Scrolling modal...")
    # El modal scrollable está en el centro de la pantalla, aproximadamente x=648, y=400
    modal_center_x, modal_center_y = 648, 450

    for step in range(8):
        scroll(ws, modal_center_x, modal_center_y, 200)
        tiktok = find_tiktok(ws)
        if tiktok:
            print(f"  TikTok encontrado en scroll {step}: ({tiktok['x']}, {tiktok['y']})")
            ss(ws, f"found_step{step}.png")
            click(ws, tiktok['x'], tiktok['y'])
            time.sleep(5)
            ss(ws, "tiktok_auth_config.png")
            url = js(ws, "window.location.href")
            print(f"  URL: {url}")

            # Buscar botón Continue/Save
            submit = js(ws, """
            (function() {
                const btns = [...document.querySelectorAll('button, a')];
                const keywords = ['Continue', 'Save', 'Next', 'Submit', 'Create', 'Use default', 'Use Composio', 'Setup'];
                const s = btns.find(b => keywords.some(k => b.textContent.trim().includes(k)));
                if (s) {
                    const r = s.getBoundingClientRect();
                    return JSON.stringify({text: s.textContent.trim().slice(0,30), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
                }
                return null;
            })()
            """)
            if submit:
                sdata = json.loads(submit)
                print(f"  Click '{sdata['text']}'")
                click(ws, sdata['x'], sdata['y'])
                time.sleep(4)
                ss(ws, "tiktok_saved.png")
            break
        print(f"    Scroll {step}: TikTok no visible todavía")

    ss(ws, "final_state.png")
    url = js(ws, "window.location.href")
    print(f"\n[FINAL] URL: {url}")
    ws.close()


if __name__ == "__main__":
    main()
