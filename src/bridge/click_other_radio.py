"""
Selecciona el radio 'Other' y crea la app de TikTok.
python -m src.bridge.click_other_radio
"""
import sys, json, time, urllib.request, base64, websocket, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
ENV = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def gws():
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

def click_xy(ws, x, y):
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


CLICK_RADIO_JS = """
(function() {
    var radios = Array.from(document.querySelectorAll('input[type="radio"]'));
    if (radios.length === 0) return "no radios";
    var radio = radios[0];
    // Force checked via native setter
    Object.defineProperty(radio, 'checked', {get: function(){return true;}, configurable:true});
    radio.setAttribute('checked', 'checked');
    radio.click();
    ['click','change','input'].forEach(function(evt) {
        radio.dispatchEvent(new Event(evt, {bubbles:true, cancelable:true}));
    });
    return "radio clicked, value=" + radio.value + " checked=" + radio.checked;
})()
"""

GET_BTN_STATE_JS = """
(function() {
    var btns = Array.from(document.querySelectorAll("button"));
    var b = btns.find(function(x) { return x.textContent.trim() === "Create app"; });
    if (!b) return "not found";
    var r = b.getBoundingClientRect();
    return JSON.stringify({
        disabled: b.disabled,
        x: Math.round(r.left + r.width/2),
        y: Math.round(r.top + r.height/2),
        text: b.textContent.trim()
    });
})()
"""

GET_CREDENTIALS_JS = """
(function() {
    var result = {};
    var text = document.body.innerText;
    // Look for Client Key pattern
    var keyMatch = text.match(/Client [Kk]ey[\\s\\S]{0,30}?([A-Za-z0-9]{8,40})/);
    var secretMatch = text.match(/Client [Ss]ecret[\\s\\S]{0,30}?([A-Za-z0-9]{8,60})/);
    if (keyMatch) result.key = keyMatch[1];
    if (secretMatch) result.secret = secretMatch[1];

    // Look in input values
    var inputs = Array.from(document.querySelectorAll("input[readonly], input[type='text']"));
    inputs.forEach(function(inp) {
        var v = inp.value.trim();
        if (v.length >= 8 && v.length <= 60 && /^[A-Za-z0-9_-]+$/.test(v)) {
            var nearby = inp.closest("tr,div,li");
            if (nearby) {
                var label = nearby.textContent.toLowerCase();
                if (label.includes("client key") || label.includes("client id")) result.key = v;
                if (label.includes("secret")) result.secret = v;
            }
        }
    });
    return JSON.stringify(result);
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
    print("CLICK OTHER RADIO + CREATE APP")
    print("=" * 60)

    ws = gws()
    if not ws:
        print("ERROR: No pestaña de TikTok Developers"); return

    cdp(ws, "Page.bringToFront", {})
    time.sleep(0.5)

    # Verificar que el modal está abierto
    page = js(ws, "document.body.innerText") or ""
    if "Create app" not in page:
        print("Modal no está abierto. Reabriendo...")
        # Abrir el modal
        open_btn = js(ws, """
        (function() {
            var btns = Array.from(document.querySelectorAll("button,a"));
            var b = btns.find(function(x) { return x.textContent.includes("Connect an app"); });
            if (b) { var r = b.getBoundingClientRect(); return JSON.stringify({x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)}); }
            return null;
        })()
        """)
        if open_btn:
            od = json.loads(open_btn)
            click_xy(ws, od["x"], od["y"])
            time.sleep(3)
        # Si hay formulario con Ownership, seleccionar Individual y Confirm
        ownership_page = js(ws, "document.body.innerText") or ""
        if "Individual" in ownership_page:
            ind = js(ws, """
            (function(){
                var radios = Array.from(document.querySelectorAll('input[type=radio]'));
                var r = radios.find(function(x){return (x.value||"").toLowerCase().includes("individual");}) || radios[0];
                if (r){r.click(); var rc=r.getBoundingClientRect(); return JSON.stringify({x:Math.round(rc.left+rc.width/2),y:Math.round(rc.top+rc.height/2)});}
                return null;
            })()
            """)
            if ind:
                id_d = json.loads(ind)
                click_xy(ws, id_d["x"], id_d["y"])
                time.sleep(0.3)
            # Confirm
            confirm = js(ws, """
            (function(){
                var b=Array.from(document.querySelectorAll("button")).find(function(x){return x.textContent.trim()==="Confirm";});
                if(b){var r=b.getBoundingClientRect(); return JSON.stringify({x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)});}
                return null;
            })()
            """)
            if confirm:
                cd_data = json.loads(confirm)
                click_xy(ws, cd_data["x"], cd_data["y"])
                time.sleep(3)
            # Ahora rellenar App name
            inp_c = js(ws, """
            (function(){
                var i=document.querySelector('input[placeholder="Enter name"],input[type=text]');
                if(i){var r=i.getBoundingClientRect(); return JSON.stringify({x:Math.round(r.left+r.width/2),y:Math.round(r.top+r.height/2)});}
                return null;
            })()
            """)
            if inp_c:
                ic = json.loads(inp_c)
                click_xy(ws, ic["x"], ic["y"])
                time.sleep(0.2)
                cdp(ws, "Input.insertText", {"text": "CurioClip"})

    # PASO 1: Click radio Other via event dispatch
    print("\n[1] Seleccionando radio 'Other' via dispatchEvent...")
    radio_result = js(ws, CLICK_RADIO_JS)
    print(f"  Result: {radio_result}")
    time.sleep(0.5)

    # Ver estado del botón
    btn_raw = js(ws, GET_BTN_STATE_JS)
    print(f"  Create app btn: {btn_raw}")
    ss(ws, "radio_clicked.png")

    if btn_raw and btn_raw != "not found":
        try:
            btn = json.loads(btn_raw)
            if not btn.get("disabled"):
                print(f"\n[2] Click Create app en ({btn['x']},{btn['y']})...")
                click_xy(ws, btn["x"], btn["y"])
                time.sleep(8)
                ss(ws, "tiktok_app_done.png")
                url = js(ws, "window.location.href")
                page2 = js(ws, "document.body.innerText") or ""
                print(f"  URL: {url}")
                print(f"  Contenido:\n{page2[:800]}")

                # Buscar credenciales
                creds_raw = js(ws, GET_CREDENTIALS_JS)
                print(f"\n  Credenciales: {creds_raw}")
                if creds_raw:
                    creds = json.loads(creds_raw)
                    if creds.get("key"):
                        print(f"\n✅ CLIENT KEY: {creds['key']}")
                        if creds.get("secret"):
                            print(f"✅ CLIENT SECRET: {creds['secret']}")
                        save_credentials(creds.get("key", "PENDIENTE"), creds.get("secret", "PENDIENTE"))
                    else:
                        print("  Credenciales no en esta vista. Buscando link de la app...")
                        app_href = js(ws, """
                        (function(){
                            var links = Array.from(document.querySelectorAll("a"));
                            var app = links.find(function(l){ return l.href && l.href.includes("/apps/") && !l.href.endsWith("/apps/") && !l.href.includes("#"); });
                            return app ? app.href : null;
                        })()
                        """)
                        if app_href:
                            print(f"  App link: {app_href}")
                            cdp(ws, "Page.navigate", {"url": app_href})
                            time.sleep(5)
                            ss(ws, "tiktok_app_detail.png")
                            page3 = js(ws, "document.body.innerText") or ""
                            print(f"  App detail:\n{page3[:800]}")
                            creds2_raw = js(ws, GET_CREDENTIALS_JS)
                            if creds2_raw:
                                creds2 = json.loads(creds2_raw)
                                if creds2.get("key"):
                                    print(f"\n✅ CLIENT KEY: {creds2['key']}")
                                    if creds2.get("secret"):
                                        print(f"✅ CLIENT SECRET: {creds2['secret']}")
                                    save_credentials(creds2.get("key", "PENDIENTE"), creds2.get("secret", "PENDIENTE"))
            else:
                print("  Create app sigue disabled.")
                print("  El radio no activó el botón. Ver radio_clicked.png")
        except json.JSONDecodeError:
            print(f"  Btn parse error: {btn_raw}")

    ws.close()


if __name__ == "__main__":
    main()
