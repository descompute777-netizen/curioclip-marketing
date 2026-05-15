"""
Captura la API key de Pexels que acaba de ser generada.
python -m src.bridge.capture_pexels_key
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_pexels_ws():
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "pexels.com" in t.get("url", ""):
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
            return ws
    return None

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

CAPTURE_KEY_JS = """
(function() {
    // Buscar en todos los inputs
    var inputs = Array.from(document.querySelectorAll("input"));
    for (var i = 0; i < inputs.length; i++) {
        var v = (inputs[i].value || "").trim();
        if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return "INPUT:" + v;
    }
    // Buscar elementos hoja de texto con formato de API key
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    var node;
    while ((node = walker.nextNode())) {
        var t = node.textContent.trim();
        if (t.length >= 32 && t.length <= 64 && /^[A-Za-z0-9]+$/.test(t)) {
            return "TEXT:" + t;
        }
    }
    // Regex en el body completo
    var body = document.body.innerText;
    var matches = body.match(/[A-Za-z0-9]{32,64}/g);
    if (matches) {
        var key = matches.find(function(m) { return m.length >= 32 && m.length <= 64; });
        if (key) return "MATCH:" + key;
    }
    return "BODY:" + body.slice(0, 800);
})()
"""


def main():
    print("=" * 50)
    print("CAPTURAR PEXELS API KEY")
    print("=" * 50)

    ws = get_pexels_ws()
    if not ws:
        print("No se encontró pestaña de Pexels")
        return

    # Navegar a la página de la key
    print("\n[NAV] pexels.com/api/key/")
    cdp(ws, "Page.navigate", {"url": "https://www.pexels.com/api/key/"})
    time.sleep(6)
    ss(ws, "pexels_final_key.png")

    url = js(ws, "window.location.href")
    print(f"  URL: {url}")

    result = js(ws, CAPTURE_KEY_JS)
    print(f"\n  Resultado: {(result or '')[:200]}")

    if result and result.startswith(("INPUT:", "TEXT:", "MATCH:")):
        key = result.split(":", 1)[1]
        print(f"\n✅ PEXELS API KEY ENCONTRADA: {key}")

        content = ENV.read_text(encoding="utf-8")
        if "PEXELS_API_KEY" in content:
            content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
        else:
            content += f"\nPEXELS_API_KEY={key}\n"
        ENV.write_text(content, encoding="utf-8")
        print("  ✅ Guardada en .env")
    else:
        # La key no fue encontrada — ver el screenshot
        print("\n  La key no se encontró en el texto de la página.")
        print("  Mira el screenshot 'pexels_final_key.png' en el directorio del proyecto.")
        print("  La key debería ser visible en la página de Pexels.")

        # También revisar si hay que ir a un dashboard
        for alt_url in [
            "https://www.pexels.com/api/",
            "https://www.pexels.com/api/new/",
        ]:
            cdp(ws, "Page.navigate", {"url": alt_url})
            time.sleep(4)
            r = js(ws, CAPTURE_KEY_JS)
            if r and r.startswith(("INPUT:", "TEXT:", "MATCH:")):
                key = r.split(":", 1)[1]
                print(f"\n✅ Key en {alt_url}: {key}")
                content = ENV.read_text(encoding="utf-8")
                if "PEXELS_API_KEY" in content:
                    content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
                else:
                    content += f"\nPEXELS_API_KEY={key}\n"
                ENV.write_text(content, encoding="utf-8")
                print("  ✅ Guardada en .env")
                break

    ws.close()


if __name__ == "__main__":
    main()
