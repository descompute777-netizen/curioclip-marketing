"""Leer el contenido del modal de productos en TikTok Developers."""
import websocket, json, urllib.request, time

def cdp_cmd(ws, msg_id, method, params=None):
    msg = {'id': msg_id, 'method': method}
    if params:
        msg['params'] = params
    ws.send(json.dumps(msg))
    for _ in range(50):
        try:
            r = json.loads(ws.recv())
            if r.get('id') == msg_id:
                return r
        except websocket.WebSocketTimeoutException:
            break
    return None

def get_ws_url():
    tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    tab = next(t for t in tabs if 'developers.tiktok.com' in t.get('url', ''))
    return tab['webSocketDebuggerUrl']

ws_url = get_ws_url()
ws = websocket.create_connection(ws_url, timeout=20)
ws.settimeout(8)

# Get full modal content
r = cdp_cmd(ws, 1, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    // Find all dialogs/modals
    var modals = document.querySelectorAll('[role=dialog]');
    var results = [];
    modals.forEach(function(m, i) {
        var t = m.textContent.trim().replace(/\s+/g, " ").substring(0, 500);
        results.push("Modal " + i + ": " + t);
    });

    // Also check for any overlay or popup
    var overlays = document.querySelectorAll('[class*="overlay"], [class*="popup"], [class*="Overlay"], [class*="Modal"]');
    overlays.forEach(function(o, i) {
        var t = o.textContent.trim().replace(/\s+/g, " ").substring(0, 300);
        results.push("Overlay " + i + ": " + t);
    });

    // Get all checkboxes (products to add may have checkboxes)
    var checkboxes = document.querySelectorAll('input[type=checkbox], [role=checkbox]');
    checkboxes.forEach(function(cb, i) {
        var label = cb.labels ? Array.from(cb.labels).map(l=>l.textContent.trim()).join(",") : "";
        var parent = cb.parentElement;
        var ctx = parent ? parent.textContent.trim().replace(/\s+/g," ").substring(0,80) : "";
        results.push("Checkbox " + i + " [" + (cb.checked?"checked":"unchecked") + "]: label=" + label + " ctx=" + ctx);
    });

    return results.join("\n---\n") || "Nothing found";
})()
''',
    'returnByValue': True
})
val = r.get('result', {}).get('result', {}).get('value', '') if r else 'ERROR'
with open('tiktok_modal_content.txt', 'w', encoding='utf-8') as f:
    f.write(val)
print(val[:3000])

# Also get buttons inside any modal
r2 = cdp_cmd(ws, 2, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    var btns = document.getElementsByTagName("button");
    var texts = Array.from(btns).map(function(b, i) {
        var t = b.textContent.trim().replace(/\s+/g, " ").substring(0, 80);
        return i + ": [" + t + "]";
    }).filter(s => s.indexOf("[]") === -1);
    return texts.join("\n");
})()
''',
    'returnByValue': True
})
val2 = r2.get('result', {}).get('result', {}).get('value', '') if r2 else ''
print("\n=== ALL BUTTONS NOW ===")
print(val2[:2000])

ws.close()
