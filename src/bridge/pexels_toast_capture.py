"""
Captura el toast/notificacion de Pexels que aparece al generar la API key.
La clave aparece en el banner inferior inmediatamente post-submit.
python -m src.bridge.pexels_toast_capture
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
        return True
    return False

def js(ws, code):
    r = cdp(ws, "Runtime.evaluate", {"expression": code, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value")

# Busca el toast/notificación en la parte inferior de la página
FIND_TOAST_JS = """
(function() {
    var results = [];

    // Buscar toasts, alerts, banners, notifications
    var selectors = [
        "[role='alert']", "[role='status']", ".toast", ".notification",
        ".alert", ".flash", ".banner", "[data-testid*='toast']",
        "[class*='toast']", "[class*='notification']", "[class*='alert']",
        "[class*='flash']", "[class*='banner']", "[class*='success']",
        "[class*='error']", "[class*='message']"
    ];

    for (var i = 0; i < selectors.length; i++) {
        var els = Array.from(document.querySelectorAll(selectors[i]));
        for (var j = 0; j < els.length; j++) {
            var t = els[j].textContent.trim();
            if (t.length > 5) results.push(selectors[i] + ": " + t.slice(0, 100));
        }
    }

    // Buscar elementos al fondo de la pantalla
    var allEls = Array.from(document.querySelectorAll("*"));
    var bottomEls = allEls.filter(function(el) {
        var r = el.getBoundingClientRect();
        return r.top > window.innerHeight * 0.7 && r.height > 20 && r.width > 200;
    });
    bottomEls.forEach(function(el) {
        var t = el.textContent.trim();
        if (t.length > 5 && t.length < 500) results.push("BOTTOM: " + t.slice(0, 100));
    });

    // Buscar inputs con posible key
    var inputs = Array.from(document.querySelectorAll("input"));
    inputs.forEach(function(inp) {
        var v = (inp.value || "").trim();
        if (v.length >= 20) results.push("INPUT_VAL: " + v);
    });

    return results.length > 0 ? results.join(" || ") : "nothing_found";
})()
"""

FILL_AND_GENERATE_JS = """
(function() {
    // Name
    var ni = Array.from(document.querySelectorAll("input[type='text'],input:not([type='checkbox']):not([type='url']):not([type='search'])"))
        .find(function(i){ return i.getBoundingClientRect().height>0; });
    if (ni) {
        var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        ns.call(ni, "CurioClip");
        ni.dispatchEvent(new Event("input",{bubbles:true}));
        ni.dispatchEvent(new Event("change",{bubbles:true}));
    }

    // Category (native select)
    var sel = document.querySelector("select");
    if (sel && sel.options.length > 1) {
        sel.value = sel.options[1].value;
        sel.dispatchEvent(new Event("change",{bubbles:true}));
    }

    // Description
    var ta = document.querySelector("textarea");
    if (ta && ta.value.trim().length < 20) {
        var ts = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
        ts.call(ta, "CurioClip social media channel using Pexels CC0 videos for TikTok.");
        ta.dispatchEvent(new Event("input",{bubbles:true}));
        ta.dispatchEvent(new Event("change",{bubbles:true}));
    }

    // ToS
    var chk = document.querySelector("input[type='checkbox']");
    if (chk && !chk.checked) chk.click();

    // Get button
    var btn = Array.from(document.querySelectorAll("button")).find(function(b){ return b.textContent.includes("Generate"); });
    if (btn) {
        var r = btn.getBoundingClientRect();
        return JSON.stringify({disabled: btn.disabled, x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2)});
    }
    return null;
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


def extract_key_from_text(text):
    """Extrae una API key (32-64 chars alfanumérico) del texto."""
    if not text: return None
    matches = re.findall(r'[A-Za-z0-9]{32,64}', text)
    for m in matches:
        if len(m) >= 32 and len(m) <= 64:
            # Filtrar palabras comunes que no son keys
            if m.lower() not in ['curioclip', 'collaboration', 'productivity', 'pexelscc', 'tiktok']:
                return m
    return None


def main():
    print("=" * 50)
    print("PEXELS TOAST CAPTURE")
    print("=" * 50)

    ws = get_ws()
    if not ws:
        print("No Pexels tab"); return

    url = js(ws, "window.location.href")
    print(f"\nURL: {url}")

    # Llenar el formulario
    print("\n[1] Llenando formulario...")
    btn_raw = js(ws, FILL_AND_GENERATE_JS)
    print(f"  Botón: {btn_raw}")

    if not btn_raw:
        print("  Error: botón no encontrado"); ws.close(); return

    btn = json.loads(btn_raw)

    # Si hay dropdown personalizado, manejarlo
    if btn.get("disabled"):
        print("  Manejando dropdown categoría...")
        click(ws, 760, 352)
        time.sleep(1.5)
        js(ws, """
        (function() {
            var opts = Array.from(document.querySelectorAll("li[role='option'],[role='option'],li"))
                .filter(function(o){ return o.getBoundingClientRect().height>0; });
            if (opts[0]) { opts[0].click(); return "ok"; }
        })()
        """)
        time.sleep(0.5)
        btn_raw = js(ws, FILL_AND_GENERATE_JS)
        if btn_raw: btn = json.loads(btn_raw)
        print(f"  Botón post-dropdown: {btn}")

    if not btn.get("disabled"):
        print(f"\n[2] CLICK Generate en ({btn['x']},{btn['y']})!")
        click(ws, btn['x'], btn['y'])

        # Captura ultra-rápida en los primeros 3 segundos (donde aparece el toast)
        print("  Capturando toast inmediatamente...")
        for i in range(15):
            time.sleep(0.5)  # Cada 500ms
            toast = js(ws, FIND_TOAST_JS)
            if toast and "nothing_found" not in str(toast):
                print(f"  [{i*0.5:.1f}s] TOAST: {toast[:200]}")
                ss(ws, f"toast_{i}.png")
                key = extract_key_from_text(toast)
                if key:
                    print(f"\n✅ PEXELS API KEY DEL TOAST: {key}")
                    save_key(key)
                    ws.close()
                    return
            else:
                # También verificar cualquier input nuevo
                new_key = js(ws, """
                (function() {
                    var inputs = Array.from(document.querySelectorAll("input"));
                    for (var i=0; i<inputs.length; i++) {
                        var v = (inputs[i].value||"").trim();
                        if (v.length >= 32 && /^[A-Za-z0-9]+$/.test(v)) return v;
                    }
                    return null;
                })()
                """)
                if new_key:
                    print(f"\n✅ KEY EN INPUT: {new_key}")
                    save_key(new_key)
                    ws.close()
                    return

        # Tomar screenshot final para diagnosis
        ss(ws, "toast_final.png")
        print("\n  Toast no capturado. Tomando screenshot diagnosis...")
        print("  Ver toast_final.png")

        # Estado final de la página
        page = js(ws, "document.body.innerText") or ""
        url = js(ws, "window.location.href")
        print(f"  URL: {url}")
        print(f"  Texto: {page[:500]}")
    else:
        print(f"  Botón aún disabled")
        ss(ws, "toast_disabled.png")

    ws.close()


if __name__ == "__main__":
    main()
