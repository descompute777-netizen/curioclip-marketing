"""
Llena el formulario de Pexels API Key y lo envía para obtener la key.
python -m src.bridge.pexels_fill_form
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_pexels_tab_ws():
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "pexels.com" in t.get("url", ""):
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
            return ws
    # Abrir nueva pestaña
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

def nav(ws, url, wait=6):
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(wait)

def click(ws, x, y):
    for t in ["mousePressed", "mouseReleased"]:
        cdp(ws, "Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})
    time.sleep(0.3)

def type_text(ws, text):
    for char in text:
        cdp(ws, "Input.insertText", {"text": char})
        time.sleep(0.03)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

def find_element_coords(ws, selector_or_text, by="selector"):
    if by == "text":
        code = f"""
        (function() {{
            var all = Array.from(document.querySelectorAll("input, textarea, select, button, a, label"));
            var el = all.find(function(e) {{ return e.textContent.trim().includes({json.dumps(selector_or_text)}) || (e.placeholder||"").includes({json.dumps(selector_or_text)}); }});
            if (el) {{
                var r = el.getBoundingClientRect();
                return JSON.stringify({{x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2), tag: el.tagName, type: el.type||""}});
            }}
            return null;
        }})()
        """
    else:
        code = f"""
        (function() {{
            var el = document.querySelector({json.dumps(selector_or_text)});
            if (el) {{
                var r = el.getBoundingClientRect();
                return JSON.stringify({{x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2), tag: el.tagName, type: el.type||""}});
            }}
            return null;
        }})()
        """
    result = js(ws, code)
    return json.loads(result) if result else None

def set_input_value(ws, selector, value):
    """Sets input value using native setter to work with React."""
    code = f"""
    (function() {{
        var el = document.querySelector({json.dumps(selector)});
        if (!el) return "not found";
        el.focus();
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        if (!setter) setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
        if (setter) {{
            setter.call(el, {json.dumps(value)});
        }} else {{
            el.value = {json.dumps(value)};
        }}
        el.dispatchEvent(new Event("input", {{bubbles: true}}));
        el.dispatchEvent(new Event("change", {{bubbles: true}}));
        return "ok:" + el.value.slice(0,20);
    }})()
    """
    return js(ws, code)

def find_key_on_page(ws):
    return js(ws, """
    (function() {
        var inputs = Array.from(document.querySelectorAll("input"));
        for (var i = 0; i < inputs.length; i++) {
            var v = (inputs[i].value || "").trim();
            if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return v;
        }
        var all = Array.from(document.querySelectorAll("*"));
        for (var i = 0; i < all.length; i++) {
            var t = all[i].textContent.trim();
            if (t.length >= 32 && t.length <= 64 && /^[A-Za-z0-9]+$/.test(t) && all[i].children.length === 0) return t;
        }
        return null;
    })()
    """)

def save_key(key):
    content = ENV.read_text(encoding="utf-8")
    if "PEXELS_API_KEY" in content:
        content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
    else:
        content += f"\nPEXELS_API_KEY={key}\n"
    ENV.write_text(content, encoding="utf-8")
    print("  Guardada en .env")


def main():
    print("=" * 50)
    print("PEXELS FORM FILL — Generando API Key")
    print("=" * 50)

    ws = get_pexels_tab_ws()

    # Navegar al formulario
    print("\n[NAV] pexels.com/api/key/")
    nav(ws, "https://www.pexels.com/api/key/", wait=5)
    ss(ws, "form_initial.png")
    url = js(ws, "window.location.href")
    print(f"  URL: {url}")

    if "key" not in url:
        print("  No estamos en el formulario. Verificar estado...")
        ss(ws, "form_debug.png")
        return

    # CAMPO 1: Project Name
    print("\n[FILL] Project Name = 'CurioClip'")
    result = set_input_value(ws, "input[name='name'], input[placeholder*='Name'], input[id*='name']", "CurioClip")
    if not result or "not found" in str(result):
        # Intentar por posición - primer input de texto
        coords = find_element_coords(ws, "input[type='text'], input:not([type])", "selector")
        if coords:
            click(ws, coords['x'], coords['y'])
            time.sleep(0.3)
            type_text(ws, "CurioClip")
            print(f"  Typed via keyboard at ({coords['x']},{coords['y']})")
        else:
            print("  Input not found, clicking at known position...")
            click(ws, 644, 307)  # Posición del primer input según screenshot
            time.sleep(0.3)
            type_text(ws, "CurioClip")
    else:
        print(f"  {result}")

    time.sleep(0.5)

    # CAMPO 2: Project Category (dropdown)
    print("\n[SELECT] Project Category = 'App/Software'")
    select_result = js(ws, """
    (function() {
        var sel = document.querySelector("select");
        if (!sel) return "no select";
        var opts = Array.from(sel.options);
        var opt = opts.find(function(o) { return o.text.includes("App") || o.text.includes("Software") || o.text.includes("Personal") || o.value; });
        if (!opt) opt = opts[1]; // Segunda opción si no encontramos
        if (opt) {
            sel.value = opt.value;
            sel.dispatchEvent(new Event("change", {bubbles: true}));
            return "selected: " + opt.text;
        }
        return "no options: " + opts.map(function(o){return o.text;}).join("|");
    })()
    """)
    print(f"  {select_result}")
    time.sleep(0.3)

    # CAMPO 3: Descripción
    print("\n[FILL] Description")
    desc = "CurioClip is a Spanish-language social media channel focused on educational curiosities and amazing science facts. We use Pexels videos as B-roll footage for our TikTok and Facebook videos. All content is used in compliance with Pexels license."
    result3 = set_input_value(ws, "textarea", desc)
    if not result3 or "not found" in str(result3):
        coords = find_element_coords(ws, "textarea", "selector")
        if coords:
            click(ws, coords['x'], coords['y'])
            time.sleep(0.3)
            type_text(ws, desc)
            print(f"  Typed via keyboard")
    else:
        print(f"  {result3}")
    time.sleep(0.3)

    # CAMPO 4: URL (opcional)
    print("\n[FILL] URL = 'https://curioclip-marketing.vercel.app'")
    js(ws, """
    (function() {
        var inputs = Array.from(document.querySelectorAll("input[type='url'], input[placeholder*='url'], input[placeholder*='URL'], input[placeholder*='website']"));
        if (inputs[0]) {
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            if (setter) setter.call(inputs[0], "https://curioclip-marketing.vercel.app");
            inputs[0].value = "https://curioclip-marketing.vercel.app";
            inputs[0].dispatchEvent(new Event("input", {bubbles: true}));
            return "ok";
        }
        return "no url input";
    })()
    """)
    time.sleep(0.3)

    # Scroll para ver checkbox y botón de submit
    cdp(ws, "Input.dispatchMouseEvent", {"type": "mouseWheel", "x": 644, "y": 400, "deltaY": 400, "deltaX": 0})
    time.sleep(1)
    ss(ws, "form_scroll.png")

    # CHECKBOX: Terms of Service
    print("\n[CHECK] Terms of Service")
    tos_result = js(ws, """
    (function() {
        var checkboxes = Array.from(document.querySelectorAll("input[type='checkbox']"));
        var tos = checkboxes.find(function(c) {
            var label = c.closest("label") || document.querySelector("label[for='" + c.id + "']");
            return (label && label.textContent.toLowerCase().includes("terms")) || c.name.toLowerCase().includes("terms") || c.id.toLowerCase().includes("terms");
        });
        if (!tos) tos = checkboxes[0]; // Primer checkbox
        if (tos && !tos.checked) {
            tos.click();
            tos.dispatchEvent(new Event("change", {bubbles: true}));
            return "checked: " + tos.id;
        }
        if (tos && tos.checked) return "already checked";
        return "no checkbox";
    })()
    """)
    print(f"  {tos_result}")
    time.sleep(0.3)

    ss(ws, "form_filled.png")

    # SUBMIT
    print("\n[SUBMIT] Enviando formulario...")
    submit_result = js(ws, """
    (function() {
        var btns = Array.from(document.querySelectorAll("button[type='submit'], input[type='submit'], button"));
        var btn = btns.find(function(b) {
            var t = b.textContent.trim().toLowerCase();
            return t.includes("generate") || t.includes("create") || t.includes("submit") || t.includes("get");
        });
        if (!btn) btn = btns[btns.length - 1];
        if (btn) {
            var r = btn.getBoundingClientRect();
            btn.click();
            return JSON.stringify({text: btn.textContent.trim().slice(0,30), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
        }
        return null;
    })()
    """)
    print(f"  Submit: {submit_result}")
    time.sleep(8)
    ss(ws, "form_submitted.png")

    url = js(ws, "window.location.href")
    print(f"  URL post-submit: {url}")

    # Buscar la API key generada
    key = find_key_on_page(ws)
    if key and len(key) >= 32:
        print(f"\n✅ PEXELS API KEY GENERADA: {key}")
        save_key(key)
    else:
        page = js(ws, "document.body.innerText") or ""
        print(f"\n  Texto visible: {page[:400]}")
        print("\n  Ver form_submitted.png para el resultado.")

    ws.close()


if __name__ == "__main__":
    main()
