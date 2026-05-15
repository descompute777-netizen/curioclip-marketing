"""
Submit final del formulario Pexels con coordenadas exactas.
Project Name(760,245) Category(760,352) ToS checkbox → Generate(760,742)
python -m src.bridge.pexels_final_submit
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_or_create_ws():
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "pexels.com" in t.get("url", ""):
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
            return ws
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        ws = websocket.WebSocket()
        ws.connect(json.loads(r.read())["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
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
    time.sleep(0.4)

def type_in(ws, text):
    cdp(ws, "Input.insertText", {"text": text})
    time.sleep(0.1)

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


def main():
    print("=" * 50)
    print("PEXELS FINAL SUBMIT — coordenadas exactas")
    print("=" * 50)

    ws = get_or_create_ws()

    # Navegar a la página y esperar que cargue completamente
    print("\n[NAV] pexels.com/api/key/")
    cdp(ws, "Page.navigate", {"url": "https://www.pexels.com/api/key/"})
    time.sleep(7)
    ss(ws, "fs_00_loaded.png")

    url = js(ws, "window.location.href")
    print(f"  URL: {url}")
    if "key" not in url:
        print("  Error: no estamos en la página del formulario")
        return

    # ACCIÓN 1: Project Name en (760, 245)
    print("\n[1] Project Name...")
    click(ws, 760, 245)
    time.sleep(0.3)

    # Ctrl+A + Delete para limpiar, luego tipear
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
    time.sleep(0.1)
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace"})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace"})
    type_in(ws, "CurioClip")
    time.sleep(0.3)

    # Verificar que se llenó
    name_val = js(ws, "document.querySelectorAll('input[type=text],input:not([type])')[0]?.value || 'no field'")
    print(f"  Project Name value: {name_val}")

    # ACCIÓN 2: Project Category — click en dropdown en (760, 352)
    print("\n[2] Category dropdown...")
    click(ws, 760, 352)
    time.sleep(2)
    ss(ws, "fs_01_dropdown.png")

    # Ver qué opciones aparecieron
    options = js(ws, """
    (function() {
        var opts = Array.from(document.querySelectorAll("[role='option'], li, .select__option, [class*='option']"));
        if (opts.length === 0) {
            // Buscar cualquier elemento que apareció después del click
            var all = Array.from(document.querySelectorAll("li, [role='menuitem'], [role='option']"));
            opts = all.filter(function(o) { return o.getBoundingClientRect().height > 0; });
        }
        return JSON.stringify(opts.slice(0, 5).map(function(o) {
            var r = o.getBoundingClientRect();
            return {text: o.textContent.trim().slice(0, 30), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)};
        }));
    })()
    """)
    print(f"  Opciones: {options}")

    if options and options != "[]":
        try:
            opts_list = json.loads(options)
            if opts_list:
                first_opt = opts_list[0]
                print(f"  Click primera opción: '{first_opt['text']}' ({first_opt['x']},{first_opt['y']})")
                click(ws, first_opt['x'], first_opt['y'])
                time.sleep(1)
        except: pass
    else:
        # Si el dropdown es nativo select, seleccionar por JS
        sel_result = js(ws, """
        (function() {
            var sel = document.querySelector("select");
            if (sel && sel.options.length > 1) {
                sel.selectedIndex = 1;
                sel.dispatchEvent(new Event("change", {bubbles: true}));
                return "native: " + sel.options[1].text;
            }
            return "no select";
        })()
        """)
        print(f"  Native select: {sel_result}")

    time.sleep(0.5)
    ss(ws, "fs_02_category_set.png")

    # ACCIÓN 3: Asegurarse que el checkbox de ToS está marcado
    print("\n[3] Terms of Service checkbox...")
    tos = js(ws, """
    (function() {
        var chk = document.querySelector("input[type='checkbox']");
        if (chk) {
            if (!chk.checked) {
                chk.click();
                return "checked";
            }
            return "already checked";
        }
        return "no checkbox";
    })()
    """)
    print(f"  ToS: {tos}")
    time.sleep(0.3)

    # ACCIÓN 4: Generate API Key en (760, 742)
    print("\n[4] Buscando botón 'Generate API Key' exacto...")
    btn_info = js(ws, """
    (function() {
        var btns = Array.from(document.querySelectorAll("button, input[type='submit']"));
        var btn = btns.find(function(b) { return b.textContent.includes("Generate") || b.value && b.value.includes("Generate"); });
        if (btn) {
            var r = btn.getBoundingClientRect();
            return JSON.stringify({text: btn.textContent.trim(), x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2), disabled: btn.disabled});
        }
        return null;
    })()
    """)
    print(f"  Botón: {btn_info}")
    ss(ws, "fs_03_before_generate.png")

    if btn_info and btn_info != "null":
        try:
            bdata = json.loads(btn_info)
            print(f"  Click 'Generate API Key' en ({bdata['x']},{bdata['y']}) disabled={bdata.get('disabled')}")
            click(ws, bdata['x'], bdata['y'])
        except: pass
    else:
        # Coordenada conocida del botón
        print(f"  Click en coordenada conocida (760, 742)...")
        click(ws, 760, 742)

    print("\n[WAIT] Esperando resultado (10s)...")
    time.sleep(10)
    ss(ws, "fs_04_result.png")

    url = js(ws, "window.location.href")
    print(f"  URL: {url}")
    page = js(ws, "document.body.innerText") or ""
    print(f"  Texto: {page[:500]}")

    # Capturar la key
    key_raw = js(ws, FIND_KEY_JS)
    print(f"\n  Key search: {key_raw}")

    if key_raw and key_raw.startswith(("INPUT:", "TEXT:")):
        key = key_raw.split(":", 1)[1]
        print(f"\n✅ PEXELS API KEY: {key}")
        content = ENV.read_text(encoding="utf-8")
        if "PEXELS_API_KEY" in content:
            content = re.sub(r"PEXELS_API_KEY=.*", f"PEXELS_API_KEY={key}", content)
        else:
            content += f"\nPEXELS_API_KEY={key}\n"
        ENV.write_text(content, encoding="utf-8")
        print("  ✅ Guardada en .env")
    else:
        print("\n  Ver fs_04_result.png para el estado final.")

    ws.close()


if __name__ == "__main__":
    main()
