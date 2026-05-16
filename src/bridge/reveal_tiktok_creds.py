"""
Revela Client Key y Secret de TikTok y añade Redirect URI de Composio.
python -m src.bridge.reveal_tiktok_creds
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
COMPOSIO_REDIRECT = "https://backend.composio.dev/api/v1/auth-apps/add"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_dev_ws():
    with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "developers.tiktok.com" in t.get("url", ""):
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

CLICK_EYE_REVEAL_JS = """
(function() {
    var results = [];
    // Buscar botones ojo/reveal junto a los campos de credentials
    var credSection = document.querySelector("[class*='credential'], [class*='Credential'], section");
    var eyeBtns = Array.from(document.querySelectorAll(
        "button[class*='eye'], button[class*='show'], button[class*='reveal'], " +
        "button[class*='toggle'], button[aria-label*='show'], button[aria-label*='reveal'], " +
        "svg[class*='eye'], [data-icon*='eye']"
    ));
    // También buscar elementos con símbolo de ojo en su contenido
    var allBtns = Array.from(document.querySelectorAll("button, span, svg, [role='button']"));
    var eyeElements = allBtns.filter(function(el) {
        var aria = (el.getAttribute("aria-label") || "").toLowerCase();
        var cls = (el.className || "").toLowerCase();
        var title = (el.title || "").toLowerCase();
        return aria.includes("show") || aria.includes("reveal") || aria.includes("eye") ||
               cls.includes("eye") || cls.includes("show") || cls.includes("reveal") ||
               title.includes("show") || title.includes("reveal");
    });
    // Click en todos los elementos ojo encontrados
    eyeElements.forEach(function(el) {
        var r = el.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) {
            el.click();
            results.push("clicked: " + (el.className || el.tagName) + " at " + Math.round(r.left+r.width/2) + "," + Math.round(r.top+r.height/2));
        }
    });
    if (results.length === 0) {
        // Buscar por posición - campos de texto con dots a su derecha
        var inputs = Array.from(document.querySelectorAll("input[type='password'], input[type='text']"));
        inputs.forEach(function(inp) {
            // El botón ojo suele estar después del input
            var next = inp.nextElementSibling;
            while (next) {
                if (next.tagName === "BUTTON" || next.tagName === "SPAN" || next.tagName === "SVG") {
                    var r = next.getBoundingClientRect();
                    if (r.width > 0 && r.height > 0 && r.width < 50) {
                        next.click();
                        results.push("sibling clicked at " + Math.round(r.left+r.width/2) + "," + Math.round(r.top+r.height/2));
                    }
                }
                next = next.nextElementSibling;
            }
        });
    }
    return results.join(" | ") || "no eye buttons found";
})()
"""

GET_REVEALED_CREDS_JS = """
(function() {
    var result = {};
    // Buscar todos los inputs visible
    var inputs = Array.from(document.querySelectorAll("input[type='text'], input:not([type='password']):not([type='radio']):not([type='checkbox'])"));
    inputs.forEach(function(inp) {
        var val = inp.value.trim();
        if (val.length >= 8 && val.length <= 80 && !/\\s/.test(val)) {
            var container = inp.closest("tr, div[class], li");
            if (container) {
                var label = container.textContent.toLowerCase();
                if (label.includes("client key") || label.includes("client id")) {
                    if (!result.key) result.key = val;
                } else if (label.includes("secret")) {
                    if (!result.secret) result.secret = val;
                }
            }
        }
    });
    // Buscar también en spans/codes que puedan mostrar el valor
    var spans = Array.from(document.querySelectorAll("span, code, td, p"));
    spans.forEach(function(sp) {
        var val = sp.textContent.trim();
        if (val.length >= 8 && val.length <= 80 && !/\\s/.test(val) && !/\\./.test(val)) {
            // No es solo puntos (dots)
            if (!/^[.•]+$/.test(val)) {
                var container = sp.closest("tr, div, li");
                if (container) {
                    var label = container.textContent.toLowerCase();
                    if ((label.includes("client key") || label.includes("client id")) && !result.key) {
                        result.key = val;
                    } else if (label.includes("secret") && !result.secret) {
                        result.secret = val;
                    }
                }
            }
        }
    });
    return JSON.stringify(result);
})()
"""

FIND_URL_PROPERTIES_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button, a, [role='button']"));
    var btn = btns.find(function(b) {
        return b.textContent.toLowerCase().includes("url properties") ||
               b.textContent.toLowerCase().includes("url prop") ||
               (b.getAttribute("href") || "").includes("url");
    });
    if (btn) {
        var r = btn.getBoundingClientRect();
        return JSON.stringify({text: btn.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
    }
    return null;
})()
"""


def save_credentials(key, secret):
    content = ENV.read_text(encoding="utf-8")
    content = re.sub(r"TIKTOK_CLIENT_KEY=.*", f"TIKTOK_CLIENT_KEY={key}", content)
    content = re.sub(r"TIKTOK_CLIENT_SECRET=.*", f"TIKTOK_CLIENT_SECRET={secret}", content)
    ENV.write_text(content, encoding="utf-8")
    print("  Guardadas en .env")


def main():
    print("=" * 60)
    print("REVEAL TIKTOK CREDENTIALS + ADD REDIRECT URI")
    print("=" * 60)

    ws = get_dev_ws()
    if not ws:
        print("No TikTok Developers tab"); return

    cdp(ws, "Page.bringToFront", {})
    time.sleep(1)

    # Paso 1: Revelar credenciales
    print("\n[1] Revelando Client Key y Secret...")
    reveal_result = js(ws, CLICK_EYE_REVEAL_JS)
    print(f"  Eye buttons: {reveal_result}")
    time.sleep(1)

    # Si no encontramos botones ojo, intentar click en posiciones conocidas del screenshot
    if "no eye buttons" in str(reveal_result):
        print("  Intentando click por coordenadas CSS del ojo...")
        # Del screenshot (1540×750): Client key eye está en ~(862, 367)
        # CSS: 862/1.48 ≈ 582, 367/1.11 ≈ 330
        click(ws, 582, 330)  # Client key eye
        time.sleep(0.5)
        # Client secret eye: ~(1335, 367) en screenshot → CSS: 902, 330
        click(ws, 902, 330)  # Client secret eye
        time.sleep(0.5)

    ss(ws, "creds_revealed.png")

    # Intentar obtener los valores
    creds_raw = js(ws, GET_REVEALED_CREDS_JS)
    creds = json.loads(creds_raw) if creds_raw else {}
    print(f"\n  Credenciales reveladas: {creds}")

    client_key = creds.get("key", "")
    client_secret = creds.get("secret", "")

    if client_key:
        print(f"\n  ✅ CLIENT KEY: {client_key}")
        if client_secret:
            print(f"  ✅ CLIENT SECRET: {client_secret}")
        save_credentials(client_key, client_secret or "PENDIENTE")
    else:
        print("  Credenciales aún ocultas. Ver creds_revealed.png")
        # Tomar screenshot para diagnóstico
        page = js(ws, "document.body.innerText") or ""
        print(f"  Texto de credenciales: {page[:400]}")

    # Paso 2: Añadir Redirect URI via "URL properties"
    print("\n[2] Abriendo URL properties...")
    url_prop_raw = js(ws, FIND_URL_PROPERTIES_JS)
    if url_prop_raw:
        up = json.loads(url_prop_raw)
        print(f"  Click '{up['text']}' en ({up['x']},{up['y']})")
        click(ws, up["x"], up["y"])
        time.sleep(4)
        ss(ws, "url_properties.png")
        page2 = js(ws, "document.body.innerText") or ""
        print(f"  URL Properties página: {page2[:400]}")

        # Buscar el campo para añadir redirect URI
        redirect_input = js(ws, """
        (function() {
            var inputs = Array.from(document.querySelectorAll("input[type='text'], input[type='url']"));
            var ri = inputs.find(function(i) {
                return (i.placeholder || "").toLowerCase().includes("redirect") ||
                       (i.placeholder || "").toLowerCase().includes("uri") ||
                       (i.placeholder || "").toLowerCase().includes("url");
            });
            if (ri) {
                var r = ri.getBoundingClientRect();
                return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2), ph: ri.placeholder});
            }
            return null;
        })()
        """)
        if redirect_input:
            ri = json.loads(redirect_input)
            print(f"  Redirect URI input encontrado: {ri}")
            click(ws, ri["x"], ri["y"])
            time.sleep(0.3)
            cdp(ws, "Input.insertText", {"text": COMPOSIO_REDIRECT})
            time.sleep(0.3)
            # Buscar botón Add/Save
            add_btn = js(ws, """
            (function() {
                var btns = Array.from(document.querySelectorAll("button"));
                var b = btns.find(function(x) {
                    return x.textContent.toLowerCase().includes("add") ||
                           x.textContent.toLowerCase().includes("save") ||
                           x.textContent.toLowerCase().includes("confirm");
                });
                if (b) { var r = b.getBoundingClientRect(); return JSON.stringify({text:b.textContent.trim(), x:Math.round(r.left+r.width/2), y:Math.round(r.top+r.height/2)}); }
                return null;
            })()
            """)
            if add_btn:
                ab = json.loads(add_btn)
                print(f"  Click '{ab['text']}'")
                click(ws, ab["x"], ab["y"])
                time.sleep(2)
                ss(ws, "redirect_added.png")
                print(f"  Redirect URI añadida!")
    else:
        print("  URL properties no encontrado como botón")
        # Buscar en la URL del sidebar
        sidebar_url = js(ws, """
        (function() {
            var links = Array.from(document.querySelectorAll("a, li"));
            var l = links.find(function(x) { return x.textContent.toLowerCase().includes("url prop"); });
            if (l) {
                var r = l.getBoundingClientRect();
                return JSON.stringify({text: l.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
            }
            return null;
        })()
        """)
        print(f"  Sidebar URL prop: {sidebar_url}")

    # Resumen
    print("\n" + "=" * 60)
    print("RESULTADO")
    print("=" * 60)
    if client_key:
        print(f"CLIENT KEY: {client_key}")
        print(f"CLIENT SECRET: {client_secret or 'ver .env'}")
        print(f"\nPróximo paso: actualizar el Composio Auth Config")
        print(f"con el Client Key correcto si difiere del actual.")
    else:
        print("Ver screenshots creds_revealed.png para el Client Key")
        print("El Client Key está visible en la UI de TikTok Developers")

    ws.close()


if __name__ == "__main__":
    main()
