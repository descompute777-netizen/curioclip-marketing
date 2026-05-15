"""
Marca el ToS checkbox y clickea Generate en Pexels.
El formulario ya tiene Name + Category + Description.
python -m src.bridge.pexels_tos_generate
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

def scroll_down(ws, dy=400):
    cdp(ws, "Input.dispatchMouseEvent", {"type": "mouseWheel", "x": 760, "y": 400, "deltaY": dy, "deltaX": 0})
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

CHECK_ALL_JS = """
(function() {
    var chk = document.querySelector("input[type='checkbox']");
    var btn = Array.from(document.querySelectorAll("button")).find(function(b) { return b.textContent.includes("Generate"); });
    var ta = document.querySelector("textarea");
    return JSON.stringify({
        checkbox_checked: chk ? chk.checked : null,
        checkbox_exists: !!chk,
        btn_disabled: btn ? btn.disabled : null,
        btn_exists: !!btn,
        desc_len: ta ? ta.value.length : 0,
        desc_preview: ta ? ta.value.slice(0, 40) : ""
    });
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
    print("PEXELS ToS + GENERATE")
    print("=" * 50)

    ws = get_ws()
    if not ws:
        print("No Pexels tab"); return

    url = js(ws, "window.location.href")
    print(f"\nURL: {url}")

    # Ver estado actual del formulario
    state_raw = js(ws, CHECK_ALL_JS)
    print(f"\nEstado del formulario: {state_raw}")

    state = json.loads(state_raw) if state_raw else {}

    # PASO 1: Marcar el checkbox si no está marcado
    print("\n[1] Checkbox ToS...")
    if not state.get("checkbox_checked") and state.get("checkbox_exists"):
        tos_result = js(ws, """
        (function() {
            var chk = document.querySelector("input[type='checkbox']");
            if (chk) {
                var r = chk.getBoundingClientRect();
                return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
            }
            return null;
        })()
        """)
        if tos_result:
            tos = json.loads(tos_result)
            print(f"  Click checkbox en ({tos['x']},{tos['y']})")
            click(ws, tos['x'], tos['y'])
            time.sleep(0.3)
            new_state = json.loads(js(ws, CHECK_ALL_JS) or "{}")
            print(f"  Checkbox ahora: checked={new_state.get('checkbox_checked')}, btn_disabled={new_state.get('btn_disabled')}")
    elif state.get("checkbox_checked"):
        print("  Ya está marcado ✅")

    # Si la checkbox no es visible, scrollear para encontrarla
    else:
        print("  Checkbox no visible en posición actual. Scrolleando...")
        scroll_down(ws, 300)
        time.sleep(0.5)
        state_raw2 = js(ws, CHECK_ALL_JS)
        state2 = json.loads(state_raw2) if state_raw2 else {}
        print(f"  Estado post-scroll: {state_raw2}")
        if state2.get("checkbox_exists") and not state2.get("checkbox_checked"):
            tos_result = js(ws, """
            (function() {
                var chk = document.querySelector("input[type='checkbox']");
                if (chk) { var r = chk.getBoundingClientRect(); return JSON.stringify({x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)}); }
                return null;
            })()
            """)
            if tos_result:
                tos = json.loads(tos_result)
                click(ws, tos['x'], tos['y'])
                print(f"  Checkbox marcado en ({tos['x']},{tos['y']})")

    # PASO 2: Ver botón y hacer click
    print("\n[2] Verificando botón Generate...")
    btn_info = js(ws, """
    (function() {
        var btns = Array.from(document.querySelectorAll("button"));
        var btn = btns.find(function(b) { return b.textContent.includes("Generate"); });
        if (btn) {
            var r = btn.getBoundingClientRect();
            return JSON.stringify({text: btn.textContent.trim(), disabled: btn.disabled, x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
        }
        return null;
    })()
    """)
    print(f"  Botón: {btn_info}")
    ss(ws, "tos_ready.png")

    if btn_info:
        btn = json.loads(btn_info)
        if not btn.get("disabled"):
            print(f"\n[3] ✅ Click Generate en ({btn['x']},{btn['y']})!")
            click(ws, btn['x'], btn['y'])
            time.sleep(12)

            # Tomar screenshot con nueva conexión (la vieja puede haber muerto)
            try:
                ss(ws, "tos_result.png")
            except Exception:
                # Re-conectar si la conexión murió
                print("  Reconectando...")
                ws2 = get_ws()
                if ws2:
                    ss(ws2, "tos_result.png")
                    url = js(ws2, "window.location.href")
                    print(f"  URL: {url}")
                    page = js(ws2, "document.body.innerText") or ""
                    print(f"  Texto: {page[:400]}")
                    key_raw = js(ws2, FIND_KEY_JS)
                    if key_raw and key_raw.startswith(("INPUT:", "TEXT:")):
                        key = key_raw.split(":", 1)[1]
                        print(f"\n✅ PEXELS API KEY: {key}")
                        save_key(key)
                    ws2.close()
                    ws.close()
                    return

            url = js(ws, "window.location.href")
            page = js(ws, "document.body.innerText") or ""
            print(f"  URL: {url}")
            print(f"  Texto: {page[:500]}")

            key_raw = js(ws, FIND_KEY_JS)
            print(f"  Key search: {key_raw}")
            if key_raw and key_raw.startswith(("INPUT:", "TEXT:")):
                key = key_raw.split(":", 1)[1]
                print(f"\n✅ PEXELS API KEY: {key}")
                save_key(key)
            else:
                print("\n  Key no encontrada en el texto.")
                print("  Mira el screenshot tos_result.png para el estado final.")
        else:
            print(f"  Botón aún disabled. Campos faltantes:")
            page = js(ws, "document.body.innerText") or ""
            lines_with_required = [l for l in page.split("\n") if "required" in l.lower() or "field" in l.lower()]
            print(f"  {lines_with_required[:5]}")
            ss(ws, "tos_disabled.png")

    ws.close()


if __name__ == "__main__":
    main()
