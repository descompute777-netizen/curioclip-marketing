"""
Crea la TikTok Developer App y extrae Client Key + Client Secret.
python -m src.bridge.create_tiktok_app
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
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
    return None

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

def find_and_click(ws, text_options):
    """Encuentra elemento por texto y hace click."""
    code = f"""
    (function() {{
        var texts = {json.dumps(text_options)};
        var all = Array.from(document.querySelectorAll("button, a, [role=button], input[type=submit]"));
        for (var i=0; i<texts.length; i++) {{
            var el = all.find(function(e) {{ return e.textContent.trim().includes(texts[i]); }});
            if (el) {{
                var r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {{
                    return JSON.stringify({{text: el.textContent.trim().slice(0,40), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)}});
                }}
            }}
        }}
        return null;
    }})()
    """
    result = js(ws, code)
    if result:
        data = json.loads(result)
        print(f"  Click '{data['text']}' en ({data['x']},{data['y']})")
        click(ws, data['x'], data['y'])
        return data
    return None

def fill_input(ws, placeholder_or_label, value):
    """Llena un input buscándolo por placeholder o label."""
    code = f"""
    (function() {{
        var inputs = Array.from(document.querySelectorAll("input, textarea"));
        var el = inputs.find(function(i) {{
            return (i.placeholder || "").toLowerCase().includes({json.dumps(placeholder_or_label.lower())})
                || (i.getAttribute("aria-label") || "").toLowerCase().includes({json.dumps(placeholder_or_label.lower())});
        }});
        if (!el) {{
            var labels = Array.from(document.querySelectorAll("label"));
            var lbl = labels.find(function(l) {{ return l.textContent.toLowerCase().includes({json.dumps(placeholder_or_label.lower())}); }});
            if (lbl) {{
                var forId = lbl.getAttribute("for");
                if (forId) el = document.getElementById(forId);
            }}
        }}
        if (el) {{
            el.focus();
            var setter = Object.getOwnPropertyDescriptor(
                el.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype,
                "value"
            ).set;
            if (setter) setter.call(el, {json.dumps(value)});
            el.value = {json.dumps(value)};
            el.dispatchEvent(new Event("input", {{bubbles:true}}));
            el.dispatchEvent(new Event("change", {{bubbles:true}}));
            var r = el.getBoundingClientRect();
            return JSON.stringify({{found:true, placeholder:el.placeholder, x:Math.round(r.left+r.width/2), y:Math.round(r.top+r.height/2)}});
        }}
        return JSON.stringify({{found:false}});
    }})()
    """
    result = js(ws, code)
    data = json.loads(result) if result else {}
    print(f"  Fill '{placeholder_or_label}' = '{value[:30]}': {data.get('found','?')}")
    return data


def extract_credentials(ws):
    """Extrae Client Key y Client Secret de la página actual."""
    page = js(ws, "document.body.innerText") or ""
    url = js(ws, "window.location.href")
    print(f"\n  Extrayendo credenciales de: {url}")

    # Buscar Client Key / Client ID
    key_patterns = [
        r"Client [Kk]ey[\s:]+([A-Za-z0-9_-]{10,})",
        r"Client [Ii][Dd][\s:]+([A-Za-z0-9_-]{10,})",
        r"App [Kk]ey[\s:]+([A-Za-z0-9_-]{10,})",
        r"[Cc]lient_key[\s:]+([A-Za-z0-9_-]{10,})",
    ]
    secret_patterns = [
        r"Client [Ss]ecret[\s:]+([A-Za-z0-9_-]{10,})",
        r"App [Ss]ecret[\s:]+([A-Za-z0-9_-]{10,})",
    ]

    client_key = None
    client_secret = None

    for pattern in key_patterns:
        m = re.search(pattern, page)
        if m:
            client_key = m.group(1)
            break

    for pattern in secret_patterns:
        m = re.search(pattern, page)
        if m:
            client_secret = m.group(1)
            break

    # También buscar en inputs/code elements
    creds_js = js(ws, """
    (function() {
        var result = {};
        var inputs = Array.from(document.querySelectorAll("input[readonly], input[type='text'], code, span, td"));
        inputs.forEach(function(el) {
            var label = "";
            var prev = el.previousElementSibling || el.closest("tr") && el.closest("tr").cells[0];
            if (prev) label = prev.textContent.toLowerCase();
            var val = (el.value || el.textContent || "").trim();
            if (val.length >= 10 && val.length <= 100 && /^[A-Za-z0-9_-]+$/.test(val)) {
                if (label.includes("key") || label.includes("id") || label.includes("client")) {
                    if (!result.key) result.key = val;
                }
                if (label.includes("secret")) {
                    if (!result.secret) result.secret = val;
                }
            }
        });
        return JSON.stringify(result);
    })()
    """)

    if creds_js:
        cdata = json.loads(creds_js)
        if cdata.get("key") and not client_key:
            client_key = cdata["key"]
        if cdata.get("secret") and not client_secret:
            client_secret = cdata["secret"]

    return client_key, client_secret


def save_credentials(client_key, client_secret):
    """Guarda las credenciales en .env."""
    content = ENV.read_text(encoding="utf-8")
    if "TIKTOK_CLIENT_KEY" not in content:
        content += f"\nTIKTOK_CLIENT_KEY={client_key}\n"
    if "TIKTOK_CLIENT_SECRET" not in content:
        content += f"TIKTOK_CLIENT_SECRET={client_secret}\n"
    ENV.write_text(content, encoding="utf-8")
    print(f"  Guardadas en .env")


def main():
    print("=" * 60)
    print("CREAR TIKTOK DEVELOPER APP")
    print("=" * 60)

    ws = get_dev_ws()
    if not ws:
        print("ERROR: No se encontró la pestaña de TikTok Developers")
        return

    # Asegurar que estamos en la página de apps
    cdp(ws, "Page.navigate", {"url": "https://developers.tiktok.com/apps/"})
    time.sleep(4)
    cdp(ws, "Page.bringToFront", {})
    ss(ws, "app_create_0_start.png")

    url = js(ws, "window.location.href")
    page = js(ws, "document.body.innerText") or ""
    print(f"\nURL: {url}")
    print(f"Estado: {page[:200]}")

    # PASO 1: Click en "Connect an app"
    print("\n[1] Click en 'Connect an app'...")
    result = find_and_click(ws, ["Connect an app", "Create an app", "Create App", "New App", "Add App"])
    if not result:
        print("  Botón no encontrado. Intentando coordenadas del screenshot...")
        click(ws, 1136, 177)  # Coordenada del botón rojo "Connect an app"
    time.sleep(4)
    ss(ws, "app_create_1_form.png")
    url2 = js(ws, "window.location.href")
    print(f"  URL post-click: {url2}")

    # Tomar screenshot para ver el formulario
    page2 = js(ws, "document.body.innerText") or ""
    print(f"  Página: {page2[:400]}")

    # PASO 2: Llenar el formulario de la app
    print("\n[2] Llenando formulario de la app...")

    # App name
    fill_input(ws, "app name", "CurioClip")
    time.sleep(0.5)

    # Description (si existe)
    fill_input(ws, "description", "Spanish-language educational social media channel on TikTok")
    time.sleep(0.5)

    # Category (puede ser un select o radio button)
    # Intentar seleccionar categoría
    cat_result = js(ws, """
    (function() {
        var sel = document.querySelector("select");
        if (sel) {
            var opts = Array.from(sel.options);
            var social = opts.find(function(o) {
                return o.text.toLowerCase().includes("social") ||
                       o.text.toLowerCase().includes("entertainment") ||
                       o.text.toLowerCase().includes("media");
            });
            if (!social) social = opts[1];
            if (social) {
                sel.value = social.value;
                sel.dispatchEvent(new Event("change",{bubbles:true}));
                return "select: " + social.text;
            }
        }
        return null;
    })()
    """)
    if cat_result:
        print(f"  Categoría: {cat_result}")

    ss(ws, "app_create_2_filled.png")

    # PASO 3: Submit el formulario
    print("\n[3] Enviando formulario...")
    submit = find_and_click(ws, ["Submit", "Create", "Connect", "Save", "Continue", "Next"])
    if not submit:
        # Intentar submit del form
        js(ws, "document.querySelector('form')?.submit()")
    time.sleep(6)
    ss(ws, "app_create_3_submitted.png")

    url3 = js(ws, "window.location.href")
    page3 = js(ws, "document.body.innerText") or ""
    print(f"  URL: {url3}")
    print(f"  Página: {page3[:500]}")

    # PASO 4: Buscar credenciales
    print("\n[4] Buscando Client Key y Client Secret...")
    client_key, client_secret = extract_credentials(ws)

    if client_key:
        print(f"\n✅ CLIENT KEY: {client_key}")
    else:
        print("  Client Key no encontrado en esta página")

    if client_secret:
        print(f"✅ CLIENT SECRET: {client_secret}")
    else:
        print("  Client Secret no encontrado (normal — puede requerir acción adicional)")

    # Si encontramos al menos el key, navegar a los detalles de la app
    if not client_key:
        print("\n  Navegando a detalles de la app...")
        app_link = js(ws, """
        (function() {
            var links = Array.from(document.querySelectorAll("a"));
            var app = links.find(function(l) {
                return l.href.includes("/apps/") && l.href.split("/").pop().length > 5;
            });
            return app ? app.href : null;
        })()
        """)
        if app_link:
            print(f"  App link: {app_link}")
            cdp(ws, "Page.navigate", {"url": app_link})
            time.sleep(4)
            ss(ws, "app_create_4_detail.png")
            page4 = js(ws, "document.body.innerText") or ""
            print(f"  Detalle: {page4[:600]}")
            client_key, client_secret = extract_credentials(ws)
            if client_key:
                print(f"\n✅ CLIENT KEY: {client_key}")
            if client_secret:
                print(f"✅ CLIENT SECRET: {client_secret}")

    # Guardar lo que encontramos
    if client_key or client_secret:
        save_credentials(client_key or "PENDIENTE", client_secret or "PENDIENTE")
        print(f"\n✅ Credenciales guardadas en .env")
        print(f"\nAhora puedes usar estas credenciales en Composio:")
        print(f"  Client ID / Client Key: {client_key or 'ver .env'}")
        print(f"  Client Secret: {client_secret or 'ver app en TikTok Developers'}")
    else:
        print("\n  Credenciales no encontradas automáticamente.")
        print("  Ver screenshots app_create_*.png para ver el estado de la app.")

    ws.close()


if __name__ == "__main__":
    main()
