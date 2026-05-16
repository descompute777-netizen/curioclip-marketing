"""Configura el Redirect URI en Login Kit de TikTok Developers."""
import websocket, json, urllib.request, time

REDIRECT_URI = "https://backend.composio.dev/api/v1/auth-apps/add"

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

# First: get the current page structure in the Products section
r = cdp_cmd(ws, 1, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    var text = document.body.innerText;
    // Find the Login Kit section
    var idx = text.indexOf("Login Kit");
    if (idx === -1) return "Login Kit NOT found in page";

    // Return surrounding context
    return "FOUND at " + idx + ": " + text.substring(idx, idx + 500).replace(/\s+/g, " ");
})()
''',
    'returnByValue': True
})
val = r.get('result', {}).get('result', {}).get('value', '') if r else ''
with open('loginkit_section.txt', 'w', encoding='utf-8') as f:
    f.write(val)
print("Login Kit section:", val[:500])
print()

# Find all inputs on the page (for Redirect URI)
r2 = cdp_cmd(ws, 2, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    var inputs = document.querySelectorAll("input, textarea");
    return Array.from(inputs).map(function(inp, i) {
        var label = inp.labels ? Array.from(inp.labels).map(l => l.textContent.trim()).join(",") : "";
        var placeholder = inp.placeholder || "";
        var val = inp.value || "";
        return i + ": type=" + inp.type + " | placeholder=" + placeholder.substring(0,60) + " | label=" + label.substring(0,60) + " | value=" + val.substring(0,60);
    }).join("\n");
})()
''',
    'returnByValue': True
})
val2 = r2.get('result', {}).get('result', {}).get('value', '') if r2 else ''
with open('page_inputs.txt', 'w', encoding='utf-8') as f:
    f.write(val2)
print("Inputs found:", val2[:2000])

ws.close()
