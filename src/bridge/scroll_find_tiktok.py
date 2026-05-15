"""
Scrollea el modal de Composio hasta encontrar TikTok y lo selecciona.
python -m src.bridge.scroll_find_tiktok
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
    time.sleep(0.2)

def scroll(ws, dy):
    cdp(ws, "Input.dispatchMouseEvent", {
        "type": "mouseWheel", "x": 648, "y": 450, "deltaY": dy, "deltaX": 0
    })
    time.sleep(0.3)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")


FIND_TIKTOK_JS = """
(function() {
    var all = Array.from(document.querySelectorAll('*'));
    for (var i = 0; i < all.length; i++) {
        var el = all[i];
        var t = el.textContent.trim();
        if (t.length < 15 && (t.toLowerCase() === 'tiktok' || t === 'TikTok')) {
            var r = el.getBoundingClientRect();
            if (r.width > 0 && r.height > 0 && r.top > 0 && r.top < window.innerHeight) {
                return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
            }
        }
    }
    return null;
})()
"""

FIND_SUBMIT_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll('button, a'));
    var keywords = ['Use default', 'Use Composio', 'Continue', 'Next', 'Save', 'Create', 'Enable'];
    var b = null;
    for (var i = 0; i < btns.length; i++) {
        var txt = btns[i].textContent.trim();
        for (var j = 0; j < keywords.length; j++) {
            if (txt.includes(keywords[j])) { b = btns[i]; break; }
        }
        if (b) break;
    }
    if (b) {
        var r = b.getBoundingClientRect();
        if (r.width > 0) return JSON.stringify({text: b.textContent.trim().slice(0,30), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
    }
    return null;
})()
"""


def main():
    print("=" * 50)
    print("SCROLL FIND TIKTOK — COMPOSIO")
    print("=" * 50)

    ws = get_ws()
    if not ws:
        print("No Composio tab"); return

    # Scroll masivo hacia la T
    print("[SCROLL] Buscando TikTok en la lista (T section)...")
    for i in range(18):
        scroll(ws, 350)
        found = js(ws, FIND_TIKTOK_JS)
        if found:
            data = json.loads(found)
            print(f"\n✅ TikTok encontrado en scroll {i}: ({data['x']}, {data['y']})")
            ss(ws, f"found_{i}.png")

            # Click en TikTok
            click(ws, data['x'], data['y'])
            time.sleep(5)
            ss(ws, "tiktok_form.png")

            url = js(ws, "window.location.href")
            print(f"  URL: {url}")

            # Buscar botón de continuar/guardar
            submit_raw = js(ws, FIND_SUBMIT_JS)
            if submit_raw:
                sdata = json.loads(submit_raw)
                print(f"  Click '{sdata['text']}' en ({sdata['x']},{sdata['y']})")
                click(ws, sdata['x'], sdata['y'])
                time.sleep(5)
                ss(ws, "tiktok_saved.png")
                final_url = js(ws, "window.location.href")
                print(f"  URL final: {final_url}")

                page = js(ws, "document.body.innerText") or ""
                if "tiktok" in page.lower() and "auth" in final_url.lower():
                    print("\n✅ Auth Config de TikTok CREADO en Composio!")
                    print("   Siguiente paso: ir a Users → crear conexión con TikTok OAuth")
            break
        if i % 3 == 0:
            ss(ws, f"scroll_{i}.png")
            print(f"    Scroll {i}: aún buscando...")

    else:
        # TikTok no encontrado después de scroll completo
        ss(ws, "bottom_list.png")
        page = js(ws, "document.body.innerText") or ""
        print(f"\n⚠️  TikTok no encontrado en la lista.")
        print(f"   Contenido visible al final: {page[:300]}")

        # Ver si el filtro funciona ahora después de tanto scroll
        result = js(ws, """
        (function() {
            var inp = document.querySelector('input');
            if (!inp) return 'no input';
            inp.focus();
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(inp, '');
            inp.dispatchEvent(new Event('input', {bubbles: true}));
            setTimeout(function() {
                setter.call(inp, 'TikTok');
                inp.dispatchEvent(new Event('input', {bubbles: true}));
            }, 500);
            return 'cleared and retyped';
        })()
        """)
        print(f"   Re-search: {result}")
        time.sleep(3)
        ss(ws, "retry_search.png")

    ws.close()


if __name__ == "__main__":
    main()
