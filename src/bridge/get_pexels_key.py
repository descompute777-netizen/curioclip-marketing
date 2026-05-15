"""
Obtiene la API key de Pexels — el usuario ya tiene cuenta (joan).
python -m src.bridge.get_pexels_key
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
ENV_PATH = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def open_tab():
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())["webSocketDebuggerUrl"]

def ws_connect(u):
    ws = websocket.WebSocket()
    ws.connect(u, timeout=10, origin="http://localhost:9222")
    return ws

def cdp(ws, m, p=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid: return r
        except: return None

def nav(ws, url, wait=6):
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(wait)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")


KEY_FIND_JS = """
(function() {
    var inputs = document.querySelectorAll("input");
    for (var i = 0; i < inputs.length; i++) {
        var v = (inputs[i].value || "").trim();
        if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return "INPUT:" + v;
    }
    var codes = document.querySelectorAll("code, pre, .api-key, [class*=key]");
    for (var i = 0; i < codes.length; i++) {
        var t = codes[i].textContent.trim();
        if (t.length >= 32 && t.length <= 100 && /^[A-Za-z0-9]+$/.test(t)) return "CODE:" + t;
    }
    var body = document.body.innerText;
    var lines = body.split("\\n");
    for (var i = 0; i < lines.length; i++) {
        var l = lines[i].trim();
        if (l.length >= 32 && l.length <= 64 && /^[A-Za-z0-9]+$/.test(l)) return "LINE:" + l;
    }
    return "BODY:" + body.slice(0, 600);
})()
"""


def save_key(key):
    content = ENV_PATH.read_text(encoding="utf-8")
    if "PEXELS_API_KEY" in content:
        content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
    else:
        content += f"\nPEXELS_API_KEY={key}\n"
    ENV_PATH.write_text(content, encoding="utf-8")
    print("  Guardada en .env")


def main():
    print("=" * 50)
    print("PEXELS API KEY — joan ya tiene cuenta")
    print("=" * 50)

    ws = ws_connect(open_tab())

    # La página API de Pexels para usuario logueado
    print("\n[NAV] pexels.com/api/ ...")
    nav(ws, "https://www.pexels.com/api/", wait=6)
    ss(ws, "pexels_api_loggedin.png")
    url = js(ws, "window.location.href")
    print(f"  URL: {url}")

    result = js(ws, KEY_FIND_JS)
    print(f"  Resultado: {(result or '')[:200]}")

    if result and result.startswith(("INPUT:", "CODE:", "LINE:")):
        key = result.split(":", 1)[1]
        print(f"\n✅ API KEY ENCONTRADA: {key}")
        save_key(key)
        ws.close()
        return

    # Si el body muestra la página pero sin key, puede necesitar click en algo
    print("\n  Key no encontrada directamente.")
    print("  Buscando botón o enlace para ver la key...")

    show_key = js(ws, """
    (function() {
        var btns = Array.from(document.querySelectorAll("button, a, span"));
        var btn = btns.find(function(b) {
            var t = b.textContent.toLowerCase();
            return t.includes("show") || t.includes("reveal") || t.includes("copy") || t.includes("api key");
        });
        if (btn) {
            var r = btn.getBoundingClientRect();
            return JSON.stringify({text: btn.textContent.trim().slice(0,30), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
        }
        return null;
    })()
    """)

    if show_key:
        data = json.loads(show_key)
        print(f"  Click '{data['text']}' en ({data['x']},{data['y']})")
        cdp(ws, "Input.dispatchMouseEvent", {"type": "mousePressed", "x": data['x'], "y": data['y'], "button": "left", "clickCount": 1})
        cdp(ws, "Input.dispatchMouseEvent", {"type": "mouseReleased", "x": data['x'], "y": data['y'], "button": "left", "clickCount": 1})
        time.sleep(2)
        result2 = js(ws, KEY_FIND_JS)
        if result2 and result2.startswith(("INPUT:", "CODE:", "LINE:")):
            key = result2.split(":", 1)[1]
            print(f"\n✅ API KEY: {key}")
            save_key(key)
            ws.close()
            return

    # Navegar a la sección específica de API keys
    print("\n  Probando URLs alternativas de la API key...")
    for url in ["https://www.pexels.com/api/new/", "https://www.pexels.com/join/api/",
                "https://www.pexels.com/explore/", "https://www.pexels.com/api/documentation/"]:
        nav(ws, url, wait=4)
        current = js(ws, "window.location.href")
        result = js(ws, KEY_FIND_JS)
        if result and result.startswith(("INPUT:", "CODE:", "LINE:")):
            key = result.split(":", 1)[1]
            print(f"\n✅ API KEY en {current}: {key}")
            save_key(key)
            ws.close()
            return

    ss(ws, "pexels_final_state.png")
    print("\n  Ver pexels_api_loggedin.png para entender qué muestra la página.")
    print("  La API key de Pexels se obtiene así:")
    print("  1. En tu Chrome: ve a pexels.com/api/")
    print("  2. La key aparece directamente (joan ya tiene cuenta)")
    print("  3. Cópiala y corre este comando:")
    print("     python -c \"import pathlib,re; p=pathlib.Path(r'C:/Users/Nick/Desktop/AGENCIA DE MARKETING/.env'); c=p.read_text(); p.write_text(c + chr(10) + 'PEXELS_API_KEY=TU_KEY_AQUI')\"")

    ws.close()


if __name__ == "__main__":
    main()
