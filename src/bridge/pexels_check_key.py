"""
Verifica si la key de Pexels ya fue generada y la captura.
python -m src.bridge.pexels_check_key
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_or_open_ws(url_hint="pexels.com"):
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if url_hint in t.get("url", ""):
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
            return ws
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        tab = json.loads(r.read())
    ws = websocket.WebSocket()
    ws.connect(tab["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
    return ws

def cdp(ws, m, p=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid: return r
        except: return None

def nav(ws, url, wait=5):
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(wait)

def click(ws, x, y):
    for t in ["mousePressed", "mouseReleased"]:
        cdp(ws, "Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})
    time.sleep(0.4)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

FIND_KEY_JS = """
(function() {
    var inputs = Array.from(document.querySelectorAll("input"));
    for (var i = 0; i < inputs.length; i++) {
        var v = (inputs[i].value || "").trim();
        if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return "INPUT:" + v;
    }
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    var node;
    while ((node = walker.nextNode())) {
        var t = node.textContent.trim();
        if (t.length >= 32 && t.length <= 64 && /^[A-Za-z0-9]+$/.test(t)) return "TEXT:" + t;
    }
    return null;
})()
"""

def save_key(key):
    content = ENV.read_text(encoding="utf-8")
    if "PEXELS_API_KEY" in content:
        content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
    else:
        content += f"\nPEXELS_API_KEY={key}\n"
    ENV.write_text(content, encoding="utf-8")
    print("  ✅ Guardada en .env")


def main():
    print("=" * 50)
    print("PEXELS KEY CHECK")
    print("=" * 50)

    ws = get_or_open_ws("pexels.com")
    url = js(ws, "window.location.href")
    print(f"\nURL actual: {url}")

    # Verificar en múltiples páginas de Pexels
    pages_to_check = [
        url,  # La página actual
        "https://www.pexels.com/api/",
        "https://www.pexels.com/api/key/",
    ]

    for page_url in pages_to_check:
        if page_url != url:
            nav(ws, page_url, wait=5)
        else:
            time.sleep(2)

        current = js(ws, "window.location.href")
        page = js(ws, "document.body.innerText") or ""
        ss(ws, f"check_{pages_to_check.index(page_url)}.png")
        print(f"\n  [{page_url}]")
        print(f"  URL: {current}")
        print(f"  Texto: {page[:200]}")

        key_raw = js(ws, FIND_KEY_JS)
        if key_raw and key_raw.startswith(("INPUT:", "TEXT:")):
            key = key_raw.split(":", 1)[1]
            print(f"\n✅ API KEY ENCONTRADA: {key}")
            save_key(key)
            ws.close()
            return

        if "Your API Key" in page or "api key" in page.lower():
            print(f"  *** 'Your API Key' encontrado en texto! Buscando valor...")

    # Si el formulario sigue ahí, hacer un último submit
    print("\n\nFormulario todavía presente. Rellenando y enviando...")
    nav(ws, "https://www.pexels.com/api/key/", wait=5)
    ss(ws, "check_form_final.png")

    # Click en textarea y tipear
    ta_info = js(ws, """
    (function() {
        var ta = document.querySelector("textarea");
        if (!ta) return null;
        var r = ta.getBoundingClientRect();
        return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
    })()
    """)

    if ta_info:
        ta = json.loads(ta_info)
        click(ws, ta['x'], ta['y'])
        time.sleep(0.3)
        # Ctrl+A y borrar
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete", "code": "Delete"})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Delete", "code": "Delete"})
        time.sleep(0.2)
        # Tipear descripción limpia
        desc = "CurioClip is a social media channel using Pexels CC0 videos as B-roll for TikTok content creation in Spanish."
        cdp(ws, "Input.insertText", {"text": desc})
        time.sleep(0.5)

        # Verificar botón y hacer click
        btn = js(ws, """
        (function() {
            var btns = Array.from(document.querySelectorAll("button"));
            var b = btns.find(function(x) { return x.textContent.includes("Generate"); });
            if (b) {
                var r = b.getBoundingClientRect();
                return JSON.stringify({disabled: b.disabled, x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
            }
            return null;
        })()
        """)
        print(f"  Botón: {btn}")

        if btn:
            bd = json.loads(btn)
            if not bd.get("disabled"):
                click(ws, bd['x'], bd['y'])
                time.sleep(10)
                ss(ws, "check_after_submit.png")
                url = js(ws, "window.location.href")
                page = js(ws, "document.body.innerText") or ""
                print(f"  URL: {url}")
                print(f"  Texto: {page[:400]}")
                key_raw = js(ws, FIND_KEY_JS)
                if key_raw and key_raw.startswith(("INPUT:", "TEXT:")):
                    key = key_raw.split(":", 1)[1]
                    print(f"\n✅ API KEY: {key}")
                    save_key(key)

    ws.close()
    print("\n[FINAL] Ver screenshots check_*.png para el estado final.")


if __name__ == "__main__":
    main()
