"""Click 'Agregar productos' en TikTok Developers y añade Login Kit + Content Posting API."""
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

print("=== STEP 1: Clicking 'Agregar productos' (button index 18) ===")
r = cdp_cmd(ws, 1, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    var btns = document.getElementsByTagName("button");
    var btn = btns[18];
    if (!btn) return "ERROR: button 18 not found, total: " + btns.length;
    var text = btn.textContent.trim();
    btn.click();
    return "Clicked: [" + text + "]";
})()
''',
    'returnByValue': True
})
result = r.get('result', {}).get('result', {}).get('value', '') if r else 'NO RESPONSE'
print("Click result:", result)

time.sleep(2)  # Wait for modal to appear

print("\n=== STEP 2: Check what appeared after click ===")
r2 = cdp_cmd(ws, 2, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    // Look for a modal or dialog
    var modals = document.querySelectorAll('[role=dialog], [role=alertdialog], .modal, [class*=modal], [class*=dialog]');
    if (modals.length > 0) {
        return "MODAL FOUND (" + modals.length + "): " + modals[0].textContent.trim().replace(/\s+/g," ").substring(0,300);
    }
    // Check if new buttons appeared
    var btns = document.getElementsByTagName("button");
    var texts = Array.from(btns).map(b => b.textContent.trim().replace(/\s+/g," ").substring(0,40)).filter(t=>t);
    return "No modal. Buttons (" + btns.length + "): " + texts.slice(0,20).join(" | ");
})()
''',
    'returnByValue': True
})
result2 = r2.get('result', {}).get('result', {}).get('value', '') if r2 else 'NO RESPONSE'
with open('tiktok_after_click.txt', 'w', encoding='utf-8') as f:
    f.write(result2)
print("After click:", result2[:500])

ws.close()
