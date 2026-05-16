"""CDP inspector for TikTok Developers tab."""
import websocket, json, urllib.request

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
    return tab['webSocketDebuggerUrl'], tab['url']

ws_url, page_url = get_ws_url()
print(f"Tab URL: {page_url}")

ws = websocket.create_connection(ws_url, timeout=20)
ws.settimeout(5)

# Get all buttons
r = cdp_cmd(ws, 1, 'Runtime.evaluate', {
    'expression': r'''
Array.from(document.getElementsByTagName("button")).map(function(b,i) {
    var t = b.textContent.trim().replace(/\s+/g," ").substring(0,80);
    var p = b.parentElement;
    var pp = p ? p.parentElement : null;
    var ctx = pp ? pp.textContent.trim().replace(/\s+/g," ").substring(0,60) : "";
    return i + ": [" + t + "] ctx: " + ctx;
}).join("\n")
''',
    'returnByValue': True
})
val = r.get('result', {}).get('result', {}).get('value', '') if r else 'ERROR'
print("=== BUTTONS ===")
print(val[:3000] if val else 'EMPTY')

# Also get all links with href
r2 = cdp_cmd(ws, 2, 'Runtime.evaluate', {
    'expression': r'''
Array.from(document.getElementsByTagName("a")).map(function(a,i) {
    var t = a.textContent.trim().replace(/\s+/g," ").substring(0,60);
    return i + ": [" + t + "] href: " + (a.href||"").substring(0,80);
}).join("\n")
''',
    'returnByValue': True
})
val2 = r2.get('result', {}).get('result', {}).get('value', '') if r2 else 'ERROR'
print("\n=== LINKS ===")
print(val2[:3000] if val2 else 'EMPTY')

ws.close()
