"""
Una sola ejecución: llena Name + Category + ToS + Generate.
SIN re-navegar la página. Trabaja sobre el formulario que ya está abierto.
python -m src.bridge.pexels_oneshot
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

# JS que llena TODOS los campos del formulario en una sola llamada
FILL_ALL_JS = """
(function() {
    var results = {};

    // === Project Name ===
    var nameInputs = Array.from(document.querySelectorAll("input[type='text'], input:not([type])"));
    var nameInput = nameInputs.find(function(i) {
        var r = i.getBoundingClientRect();
        return r.height > 0 && r.width > 0;
    });
    if (nameInput) {
        nameInput.focus();
        var nameSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nameSetter.call(nameInput, "CurioClip");
        nameInput.dispatchEvent(new Event("input", {bubbles: true}));
        nameInput.dispatchEvent(new Event("change", {bubbles: true}));
        results.name = "OK:" + nameInput.value;
    } else {
        results.name = "NOT FOUND";
    }

    // === Category ===
    var sel = document.querySelector("select");
    if (sel && sel.options.length > 1) {
        sel.selectedIndex = 1;
        sel.dispatchEvent(new Event("change", {bubbles: true}));
        results.category = "SELECT:" + (sel.options[1] ? sel.options[1].text : "?");
    } else {
        // Custom dropdown - find by placeholder text or role
        var dropdowns = Array.from(document.querySelectorAll("[role='combobox'], [aria-haspopup], button"));
        var dd = dropdowns.find(function(d) {
            return (d.textContent || "").includes("Category") || (d.textContent || "").includes("Select");
        });
        if (dd) {
            var r = dd.getBoundingClientRect();
            results.category = "CUSTOM_DROPDOWN:" + Math.round(r.left+r.width/2) + "," + Math.round(r.top+r.height/2);
        } else {
            results.category = "NOT FOUND";
        }
    }

    // === Description (only if empty) ===
    var ta = document.querySelector("textarea");
    if (ta && ta.value.trim().length < 10) {
        ta.focus();
        var taSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
        taSetter.call(ta, "CurioClip uses Pexels CC0 videos as B-roll for Spanish TikTok content.");
        ta.dispatchEvent(new Event("input", {bubbles: true}));
        ta.dispatchEvent(new Event("change", {bubbles: true}));
        results.desc = "FILLED";
    } else if (ta) {
        results.desc = "ALREADY:" + ta.value.length;
    }

    // === ToS Checkbox ===
    var chk = document.querySelector("input[type='checkbox']");
    if (chk) {
        if (!chk.checked) {
            chk.click();
            chk.dispatchEvent(new Event("change", {bubbles: true}));
        }
        results.tos = chk.checked ? "CHECKED" : "NOT CHECKED";
        var cr = chk.getBoundingClientRect();
        results.tos_coords = Math.round(cr.left+cr.width/2) + "," + Math.round(cr.top+cr.height/2);
    } else {
        results.tos = "NOT FOUND";
    }

    // === Button state ===
    var btn = Array.from(document.querySelectorAll("button")).find(function(b) { return b.textContent.includes("Generate"); });
    if (btn) {
        var br = btn.getBoundingClientRect();
        results.btn = "disabled:" + btn.disabled + " at " + Math.round(br.left+br.width/2) + "," + Math.round(br.top+br.height/2);
        results.btn_disabled = btn.disabled;
        results.btn_x = Math.round(br.left+br.width/2);
        results.btn_y = Math.round(br.top+br.height/2);
    }

    return JSON.stringify(results);
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
    print("PEXELS ONESHOT — Todo en un solo paso")
    print("=" * 50)

    ws = get_ws()
    if not ws:
        print("No Pexels tab"); return

    url = js(ws, "window.location.href")
    print(f"\nURL: {url}")
    ss(ws, "oneshot_before.png")

    # Ejecutar el fill completo
    print("\n[1] Llenando todos los campos...")
    result_raw = js(ws, FILL_ALL_JS)
    print(f"  Resultado: {result_raw}")

    if not result_raw:
        print("  Error ejecutando JS"); ws.close(); return

    result = json.loads(result_raw)

    # Manejar categoria custom (dropdown que requiere click y selección)
    if result.get("category", "").startswith("CUSTOM_DROPDOWN:"):
        coords = result["category"].split(":")[1].split(",")
        cx, cy = int(coords[0]), int(coords[1])
        print(f"\n  Category dropdown custom en ({cx},{cy})...")
        click(ws, cx, cy)
        time.sleep(2)

        # Seleccionar primera opción
        opt_result = js(ws, """
        (function() {
            var opts = Array.from(document.querySelectorAll("[role='option'], li, .select__option"));
            if (opts.length === 0) {
                opts = Array.from(document.querySelectorAll("li")).filter(function(l) {
                    return l.getBoundingClientRect().height > 0;
                });
            }
            if (opts[0]) {
                var r = opts[0].getBoundingClientRect();
                opts[0].click();
                return "clicked: " + opts[0].textContent.trim();
            }
            return "no options";
        })()
        """)
        print(f"  Category option: {opt_result}")
        time.sleep(0.5)

    # Re-ejecutar fill para asegurar que ToS esté marcado
    print("\n[2] Re-verificando estado...")
    result2_raw = js(ws, FILL_ALL_JS)
    result2 = json.loads(result2_raw) if result2_raw else {}
    print(f"  Estado: {result2_raw}")
    ss(ws, "oneshot_filled.png")

    # Si el ToS sigue sin marcar, click directo
    if result2.get("tos") != "CHECKED" and result2.get("tos_coords"):
        coords2 = result2["tos_coords"].split(",")
        cx2, cy2 = int(coords2[0]), int(coords2[1])
        print(f"\n  Click ToS en ({cx2},{cy2})...")
        click(ws, cx2, cy2)
        time.sleep(0.5)

    # Verificar estado final del botón
    btn_x = result2.get("btn_x", 760)
    btn_y = result2.get("btn_y", 742)
    btn_disabled = result2.get("btn_disabled", True)

    print(f"\n[3] Botón Generate: disabled={btn_disabled} en ({btn_x},{btn_y})")

    if not btn_disabled:
        print(f"  ✅ Botón habilitado. Click...")
        click(ws, btn_x, btn_y)

        print("  Esperando respuesta (12s)...")
        time.sleep(12)

        # Re-conectar si es necesario
        try:
            ss(ws, "oneshot_result.png")
            url = js(ws, "window.location.href")
            page = js(ws, "document.body.innerText") or ""
            print(f"  URL: {url}")
            print(f"  Texto: {page[:400]}")
            key_raw = js(ws, FIND_KEY_JS)
            if key_raw and key_raw.startswith(("INPUT:", "TEXT:")):
                key = key_raw.split(":", 1)[1]
                print(f"\n✅ PEXELS API KEY: {key}")
                save_key(key)
            else:
                print("\n  Key no en el texto. Ver oneshot_result.png")
        except Exception as e:
            print(f"  Connection error post-submit: {e}")
            print("  Ver tu Chrome para el resultado")
    else:
        print(f"\n  ⚠️ Botón aún disabled.")
        print(f"  Estado completo: {result2}")
        ss(ws, "oneshot_still_disabled.png")

    ws.close()


if __name__ == "__main__":
    main()
