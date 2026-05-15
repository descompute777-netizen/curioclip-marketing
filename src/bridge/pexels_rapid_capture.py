"""
Genera y captura la key de Pexels inmediatamente post-submit.
Toma screenshot cada 2s durante 20s para no perderse la key.
python -m src.bridge.pexels_rapid_capture
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_ws():
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

def click(ws, x, y):
    for t in ["mousePressed", "mouseReleased"]:
        cdp(ws, "Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})
    time.sleep(0.1)

def ss(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f: f.write(base64.b64decode(data))

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

FILL_AND_SUBMIT_JS = """
(function() {
    var log = [];

    // Name
    var nameInputs = Array.from(document.querySelectorAll("input[type='text'],input:not([type='checkbox']):not([type='url']):not([type='search'])"));
    var ni = nameInputs.find(function(i){ var r=i.getBoundingClientRect(); return r.height>0 && i.value.trim()==="";});
    if (!ni) ni = nameInputs[0];
    if (ni) {
        var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        ns.call(ni, "CurioClip");
        ni.dispatchEvent(new Event("input",{bubbles:true}));
        ni.dispatchEvent(new Event("change",{bubbles:true}));
        log.push("name:OK");
    }

    // Category - native select
    var sel = document.querySelector("select");
    if (sel && sel.options.length > 1) {
        sel.value = sel.options[1].value;
        sel.dispatchEvent(new Event("change",{bubbles:true}));
        log.push("cat:SELECT:" + sel.options[1].text);
    }

    // Description
    var ta = document.querySelector("textarea");
    if (ta && ta.value.trim().length < 20) {
        var ts = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
        ts.call(ta, "CurioClip is a Spanish social media channel using Pexels CC0 videos for TikTok content.");
        ta.dispatchEvent(new Event("input",{bubbles:true}));
        ta.dispatchEvent(new Event("change",{bubbles:true}));
        log.push("desc:FILLED");
    } else if (ta) {
        log.push("desc:EXISTS:" + ta.value.length);
    }

    // ToS
    var chk = document.querySelector("input[type='checkbox']");
    if (chk && !chk.checked) {
        chk.click();
        log.push("tos:CLICKED");
    } else if (chk) {
        log.push("tos:ALREADY_CHECKED");
    }

    // Button state
    var btn = Array.from(document.querySelectorAll("button")).find(function(b){ return b.textContent.includes("Generate"); });
    if (btn) {
        var r = btn.getBoundingClientRect();
        log.push("btn:disabled=" + btn.disabled + ":x=" + Math.round(r.left+r.width/2) + ":y=" + Math.round(r.top+r.height/2));
    }

    return log.join("|");
})()
"""

RAPID_KEY_SEARCH_JS = """
(function() {
    // Scroll to top first
    window.scrollTo(0, 0);

    // Search inputs
    var inputs = Array.from(document.querySelectorAll("input"));
    for (var i=0; i<inputs.length; i++) {
        var v = (inputs[i].value||"").trim();
        if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return "INPUT:" + v;
    }

    // All text nodes
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    var node;
    while ((node = walker.nextNode())) {
        var t = node.textContent.trim();
        if (t.length >= 32 && t.length <= 64 && /^[A-Za-z0-9]+$/.test(t)) return "TEXT:" + t;
    }

    // Full body text for debugging
    return "BODY:" + document.body.innerText.slice(0,300);
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
    print("PEXELS RAPID CAPTURE")
    print("=" * 50)

    ws = get_ws()
    if not ws:
        print("No Pexels tab"); return

    url = js(ws, "window.location.href")
    print(f"\nURL: {url}")

    # Llenar formulario y obtener estado del botón
    print("\n[1] Llenando formulario completo...")
    fill_result = js(ws, FILL_AND_SUBMIT_JS)
    print(f"  {fill_result}")
    time.sleep(0.5)

    # Si la categoría no es nativa, hacer click en dropdown y seleccionar
    if fill_result and "cat:SELECT" not in fill_result:
        print("  Manejando dropdown personalizado de categoría...")
        click(ws, 760, 352)
        time.sleep(1.5)
        opt = js(ws, """
        (function() {
            var opts = Array.from(document.querySelectorAll("li[role='option'], [role='option'], li"));
            var o = opts.find(function(x){ return x.getBoundingClientRect().height > 0; });
            if (o) { o.click(); return o.textContent.trim(); }
            return null;
        })()
        """)
        print(f"  Opción seleccionada: {opt}")
        time.sleep(0.5)

        # Re-llenar después del dropdown
        fill_result2 = js(ws, FILL_AND_SUBMIT_JS)
        print(f"  Post-dropdown: {fill_result2}")

    # Encontrar botón y hacer click
    btn_info = js(ws, """
    (function() {
        var btn = Array.from(document.querySelectorAll("button")).find(function(b){ return b.textContent.includes("Generate"); });
        if (btn) {
            var r = btn.getBoundingClientRect();
            return JSON.stringify({disabled: btn.disabled, x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
        }
        return null;
    })()
    """)
    print(f"\n[2] Botón: {btn_info}")

    if not btn_info:
        print("  Botón no encontrado"); ws.close(); return

    btn = json.loads(btn_info)
    if btn.get("disabled"):
        # Intentar scroll para ver todo el formulario y re-verificar
        cdp(ws, "Input.dispatchMouseEvent", {"type": "mouseWheel", "x": 760, "y": 400, "deltaY": 200, "deltaX": 0})
        time.sleep(0.3)
        # Click en checkbox
        chk = js(ws, """
        (function() {
            var c = document.querySelector("input[type='checkbox']");
            if (c && !c.checked) { c.click(); return "clicked"; }
            return c ? "was_checked" : "no_checkbox";
        })()
        """)
        print(f"  Checkbox: {chk}")
        time.sleep(0.3)

        btn_info2 = js(ws, """
        (function() {
            var btn = Array.from(document.querySelectorAll("button")).find(function(b){ return b.textContent.includes("Generate"); });
            if (btn) { var r=btn.getBoundingClientRect(); return JSON.stringify({disabled:btn.disabled,x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)}); }
            return null;
        })()
        """)
        print(f"  Botón post-checkbox: {btn_info2}")
        if btn_info2:
            btn = json.loads(btn_info2)

    if not btn.get("disabled"):
        print(f"\n[3] ✅ CLICK Generate en ({btn['x']},{btn['y']})!")
        click(ws, btn['x'], btn['y'])

        # Captura rápida cada 2 segundos durante 20 segundos
        print("  Capturando key con polling rápido...")
        for i in range(10):
            time.sleep(2)
            try:
                key_raw = js(ws, RAPID_KEY_SEARCH_JS)
                current_url = js(ws, "window.location.href")
                print(f"  [{i*2}s] URL={current_url} | Key={str(key_raw)[:60]}")
                ss(ws, f"rapid_{i}.png")

                if key_raw and key_raw.startswith(("INPUT:", "TEXT:")):
                    key = key_raw.split(":", 1)[1]
                    print(f"\n✅ PEXELS API KEY CAPTURADA: {key}")
                    save_key(key)
                    ws.close()
                    return
            except Exception as e:
                print(f"  [{i*2}s] Error: {e}")

        # Si no encontramos la key, mostrar el estado final
        print("\n  Key no capturada en los 20 segundos.")
        print("\n  Estado del Chrome ahora (tu Chrome debe mostrar algo):")
        try:
            final_url = js(ws, "window.location.href")
            final_page = js(ws, "document.body.innerText") or ""
            print(f"  URL: {final_url}")
            print(f"  Texto: {final_page[:400]}")
        except: pass
    else:
        print(f"\n  Botón aún disabled: {btn}")
        ss(ws, "rapid_disabled.png")

    ws.close()


if __name__ == "__main__":
    main()
