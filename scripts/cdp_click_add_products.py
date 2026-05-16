"""Clickea Add junto a Login Kit y Content Posting API en el modal de TikTok Developers."""
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

# Step 1: Find all buttons and their modal context
r = cdp_cmd(ws, 1, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    var btns = Array.from(document.getElementsByTagName("button"));
    return btns.map(function(b, i) {
        var t = b.textContent.trim().replace(/\s+/g, " ").substring(0, 60);
        // Get 3-level parent context for placement
        var p1 = b.parentElement;
        var p2 = p1 ? p1.parentElement : null;
        var p3 = p2 ? p2.parentElement : null;
        var ctx = p3 ? p3.textContent.trim().replace(/\s+/g, " ").substring(0, 100) : "";
        return i + "|" + t + "|" + ctx;
    }).join("\n");
})()
''',
    'returnByValue': True
})
val = r.get('result', {}).get('result', {}).get('value', '') if r else ''
with open('tiktok_buttons_with_ctx.txt', 'w', encoding='utf-8') as f:
    f.write(val)

# Find the "Add" button next to "Login Kit"
lines = val.split('\n')
login_kit_add_idx = None
content_posting_add_idx = None

for line in lines:
    parts = line.split('|', 2)
    if len(parts) < 2:
        continue
    idx, btn_text, ctx = parts[0], parts[1], parts[2] if len(parts) > 2 else ''

    if btn_text.strip() == 'Add' and 'Login Kit' in ctx:
        login_kit_add_idx = int(idx)
        print(f"Found Login Kit Add button: index {login_kit_add_idx}")
    elif btn_text.strip() == 'Add' and 'Content Posting API' in ctx:
        content_posting_add_idx = int(idx)
        print(f"Found Content Posting API Add button: index {content_posting_add_idx}")

# Step 2: Click Add for Login Kit
if login_kit_add_idx is not None:
    print(f"\nClicking Add for Login Kit (button {login_kit_add_idx})...")
    r2 = cdp_cmd(ws, 2, 'Runtime.evaluate', {
        'expression': f'''
(function() {{
    var btns = document.getElementsByTagName("button");
    var btn = btns[{login_kit_add_idx}];
    if (!btn) return "ERROR: button not found";
    btn.click();
    return "Clicked: [" + btn.textContent.trim() + "]";
}})()
''',
        'returnByValue': True
    })
    result = r2.get('result', {}).get('result', {}).get('value', '') if r2 else 'NO RESPONSE'
    print("Result:", result)
    time.sleep(2)

    # Check state after click
    r_check = cdp_cmd(ws, 3, 'Runtime.evaluate', {
        'expression': r'''
(function() {
    var btns = Array.from(document.getElementsByTagName("button"));
    var addedBtns = btns.filter(b => b.textContent.trim() === "Added");
    var addBtns = btns.filter(b => b.textContent.trim() === "Add");
    return "Added buttons: " + addedBtns.length + " | Add buttons: " + addBtns.length;
})()
''',
        'returnByValue': True
    })
    check_val = r_check.get('result', {}).get('result', {}).get('value', '') if r_check else ''
    print("After click:", check_val)
else:
    print("ERROR: Could not find Login Kit Add button")
    print("Lines found:", [l for l in lines if 'Add' in l][:10])

ws.close()
