"""Inspecciona los inputs de texto sin label para encontrar el Redirect URI de Login Kit."""
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

# Get surrounding context for each input
r = cdp_cmd(ws, 1, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    var inputs = document.querySelectorAll("input[type=text], textarea");
    return Array.from(inputs).map(function(inp, i) {
        // Walk up 5 levels to get context
        var el = inp;
        var contexts = [];
        for (var j = 0; j < 6; j++) {
            el = el.parentElement;
            if (!el) break;
            var t = el.textContent.trim().replace(/\s+/g, " ").substring(0, 100);
            contexts.push(j + "=" + t);
        }
        return "INPUT " + i + " [" + (inp.value||"empty") + "]:\n  " + contexts.slice(0,3).join("\n  ");
    }).join("\n\n");
})()
''',
    'returnByValue': True
})
val = r.get('result', {}).get('result', {}).get('value', '') if r else 'ERROR'
with open('inputs_context.txt', 'w', encoding='utf-8') as f:
    f.write(val)
print(val[:4000])
ws.close()
