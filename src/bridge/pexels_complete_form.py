"""
Completa los campos faltantes de Pexels (Name + Category) y envía.
python -m src.bridge.pexels_complete_form
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
    # Nueva pestaña
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        tab = json.loads(r.read())
    ws = websocket.WebSocket()
    ws.connect(tab["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
    cdp_send(ws, "Page.navigate", {"url": "https://www.pexels.com/api/key/"})
    time.sleep(6)
    return ws

def cdp_send(ws, m, p=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid: return r
        except: return None

def click(ws, x, y):
    for t in ["mousePressed", "mouseReleased"]:
        cdp_send(ws, "Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})
    time.sleep(0.3)

def type_in(ws, text):
    cdp_send(ws, "Input.insertText", {"text": text})
    time.sleep(0.2)

def scroll_to_top(ws):
    cdp_send(ws, "Input.dispatchMouseEvent", {"type": "mouseWheel", "x": 640, "y": 400, "deltaY": -3000, "deltaX": 0})
    time.sleep(1)

def ss(ws, path):
    r = cdp_send(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")

def js(ws, code):
    r = cdp_send(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

def find_key_on_page(ws):
    return js(ws, """
    (function() {
        var inputs = Array.from(document.querySelectorAll("input"));
        for (var i = 0; i < inputs.length; i++) {
            var v = (inputs[i].value || "").trim();
            if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return v;
        }
        var spans = Array.from(document.querySelectorAll("span, p, code, div"));
        for (var i = 0; i < spans.length; i++) {
            var t = spans[i].textContent.trim();
            if (t.length >= 32 && t.length <= 64 && /^[A-Za-z0-9]+$/.test(t) && spans[i].children.length === 0) return t;
        }
        return null;
    })()
    """)


def main():
    print("=" * 50)
    print("PEXELS COMPLETE FORM — Name + Category")
    print("=" * 50)

    ws = get_pexels_ws()

    # Scroll al top del formulario
    print("\n[SCROLL] Subiendo al inicio del formulario...")
    scroll_to_top(ws)
    ss(ws, "form_top.png")

    # Ver qué campos hay en el tope
    fields_info = js(ws, """
    (function() {
        var all = Array.from(document.querySelectorAll("input, textarea, select, button, [role=combobox], [role=listbox]"));
        return JSON.stringify(all.map(function(el) {
            var r = el.getBoundingClientRect();
            return {
                tag: el.tagName, type: el.type||"", placeholder: el.placeholder||"",
                value: (el.value||"").slice(0,20), name: el.name||"",
                x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2),
                visible: r.width > 0 && r.height > 0
            };
        }).filter(function(e){return e.visible;}));
    })()
    """)

    try:
        fields = json.loads(fields_info or "[]")
        print(f"\n  Campos visibles:")
        for f in fields:
            print(f"    {f['tag']} type={f['type']} placeholder='{f['placeholder']}' value='{f['value']}' at ({f['x']},{f['y']})")
    except: pass

    # CAMPO 1: Project Name — click en el primer input vacío visible
    print("\n[FILL] Project Name...")
    name_filled = js(ws, """
    (function() {
        var inputs = Array.from(document.querySelectorAll("input[type='text'], input:not([type])"));
        var empty = inputs.find(function(i) { return !i.value && i.getBoundingClientRect().height > 0; });
        if (!empty) empty = inputs[0];
        if (empty) {
            empty.focus();
            empty.click();
            var r = empty.getBoundingClientRect();
            return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2), ph: empty.placeholder});
        }
        return null;
    })()
    """)

    if name_filled:
        ndata = json.loads(name_filled)
        print(f"  Click en campo '{ndata['ph']}' ({ndata['x']},{ndata['y']})")
        click(ws, ndata['x'], ndata['y'])
        time.sleep(0.3)
        # Limpiar y tipear
        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Control+a", "code": "KeyA", "modifiers": 2})
        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp_send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Delete", "code": "Delete"})
        type_in(ws, "CurioClip")
        print(f"  Typed: CurioClip")
    time.sleep(0.5)

    # CAMPO 2: Category — es un select nativo o un custom dropdown
    print("\n[SELECT] Project Category...")

    # Ver opciones del select
    category_result = js(ws, """
    (function() {
        var sel = document.querySelector("select");
        if (sel) {
            var opts = Array.from(sel.options);
            // Seleccionar primera opción no vacía
            var opt = opts.find(function(o) { return o.value && o.value !== ""; });
            if (opt) {
                sel.value = opt.value;
                sel.dispatchEvent(new Event("change", {bubbles: true}));
                return "native select: " + opt.text;
            }
            return "select empty options: " + opts.map(function(o){return o.text+"="+o.value;}).join("|");
        }
        // Buscar custom dropdown
        var dropdowns = Array.from(document.querySelectorAll("[role='combobox'], [role='listbox'], [aria-haspopup]"));
        if (dropdowns.length > 0) {
            var r = dropdowns[0].getBoundingClientRect();
            return JSON.stringify({type: "custom", x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
        }
        return "no dropdown found";
    })()
    """)
    print(f"  Category: {category_result}")

    if category_result and "custom" in str(category_result):
        try:
            cdata = json.loads(category_result)
            # Click en el dropdown personalizado
            click(ws, cdata['x'], cdata['y'])
            time.sleep(2)
            ss(ws, "dropdown_open.png")

            # Seleccionar primera opción visible
            option_click = js(ws, """
            (function() {
                var opts = Array.from(document.querySelectorAll("[role='option'], li, .option"));
                if (opts.length > 0) {
                    var r = opts[0].getBoundingClientRect();
                    opts[0].click();
                    return "clicked: " + opts[0].textContent.trim();
                }
                return null;
            })()
            """)
            print(f"  Option click: {option_click}")
        except: pass
    elif "native select" in str(category_result):
        print(f"  {category_result}")
    time.sleep(0.5)

    ss(ws, "form_complete.png")

    # Ver estado del botón
    btn_state = js(ws, """
    (function() {
        var btn = document.querySelector("button[type='submit'], button");
        if (!btn) return "no button";
        var r = btn.getBoundingClientRect();
        return JSON.stringify({
            text: btn.textContent.trim(),
            disabled: btn.disabled,
            x: Math.round(r.left+r.width/2),
            y: Math.round(r.top+r.height/2)
        });
    })()
    """)
    print(f"\n  Botón: {btn_state}")

    # Scroll al submit y click
    cdp_send(ws, "Input.dispatchMouseEvent", {"type": "mouseWheel", "x": 640, "y": 400, "deltaY": 500, "deltaX": 0})
    time.sleep(1)
    ss(ws, "before_submit.png")

    # Submit
    print("\n[SUBMIT]")
    submit_result = js(ws, """
    (function() {
        var btns = Array.from(document.querySelectorAll("button"));
        var btn = btns.find(function(b) { return b.textContent.includes("Generate") || b.textContent.includes("Create"); });
        if (!btn) btn = btns[btns.length - 1];
        if (btn) {
            btn.click();
            return "clicked: " + btn.textContent.trim() + " disabled=" + btn.disabled;
        }
        return null;
    })()
    """)
    print(f"  {submit_result}")
    time.sleep(8)
    ss(ws, "after_submit.png")

    url = js(ws, "window.location.href")
    print(f"  URL: {url}")

    key = find_key_on_page(ws)
    if key and len(key) >= 32:
        print(f"\n✅ PEXELS API KEY: {key}")
        content = ENV.read_text(encoding="utf-8")
        if "PEXELS_API_KEY" in content:
            content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
        else:
            content += f"\nPEXELS_API_KEY={key}\n"
        ENV.write_text(content, encoding="utf-8")
        print("  ✅ Guardada en .env")
    else:
        page = js(ws, "document.body.innerText") or ""
        print(f"\n  Texto: {page[:400]}")

    ws.close()


if __name__ == "__main__":
    main()
