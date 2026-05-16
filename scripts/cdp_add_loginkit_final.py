"""Añadir Login Kit y Content Posting API en el modal de TikTok Developers."""
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

def find_and_click_product(ws, cmd_start, keyword):
    """Find the Add button for a specific product (by description keyword) and click it."""
    expr = f'''
(function() {{
    // Find the modal
    var allEls = document.querySelectorAll("div");
    var modal = null;
    for (var i = 0; i < allEls.length; i++) {{
        var t = allEls[i].textContent;
        if (t.includes("Login Kit") && t.includes("Content Posting") && t.includes("Share Kit")) {{
            if (!modal || t.length < modal.textContent.length) modal = allEls[i];
        }}
    }}
    if (!modal) return "MODAL NOT FOUND";

    var btns = Array.from(modal.querySelectorAll("button"));
    for (var j = 0; j < btns.length; j++) {{
        var btn = btns[j];
        var btnText = btn.textContent.trim();
        if (btnText !== "Add") continue;
        // Check the parent row context
        var parent = btn.parentElement;
        var rowText = parent ? parent.previousElementSibling ? parent.previousElementSibling.textContent : "" : "";
        if (rowText.includes("{keyword}")) {{
            btn.click();
            return "CLICKED Add for product with keyword: {keyword} (btn " + j + ")";
        }}
    }}
    return "NOT FOUND: No Add button found near keyword: {keyword}";
}})()
'''
    r = cdp_cmd(ws, cmd_start, 'Runtime.evaluate', {'expression': expr, 'returnByValue': True})
    return r.get('result', {}).get('result', {}).get('value', 'NO RESPONSE') if r else 'NO RESPONSE'

# Step 1: Add Login Kit
print("=== Adding Login Kit ===")
result = find_and_click_product(ws, 1, "quick and secure way to log in")
print("Result:", result)
time.sleep(2)

# Verify state
r_check = cdp_cmd(ws, 2, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    var btns = Array.from(document.getElementsByTagName("button"));
    var added = btns.filter(b => b.textContent.trim() === "Added").map(b => "Added");
    var add_btns = btns.filter(b => b.textContent.trim() === "Add").map(b => "Add");
    return "Added: " + added.length + " | Add: " + add_btns.length;
})()
''',
    'returnByValue': True
})
check = r_check.get('result', {}).get('result', {}).get('value', '') if r_check else ''
print("State after Login Kit:", check)

time.sleep(1)

# Step 2: Add Content Posting API
print("\n=== Adding Content Posting API ===")
result2 = find_and_click_product(ws, 3, "draft or a direct post")
print("Result:", result2)
time.sleep(2)

# Final check
r_final = cdp_cmd(ws, 4, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    var modal = null;
    var divs = document.querySelectorAll("div");
    for (var i=0; i<divs.length; i++) {
        var t = divs[i].textContent;
        if (t.includes("Login Kit") && t.includes("Content Posting") && t.includes("Share Kit")) {
            if (!modal || t.length < modal.textContent.length) modal = divs[i];
        }
    }
    if (!modal) return "Modal gone";
    var btns = Array.from(modal.querySelectorAll("button"));
    return btns.map(function(b,i){ return i+":"+b.textContent.trim(); }).join("|");
})()
''',
    'returnByValue': True
})
final = r_final.get('result', {}).get('result', {}).get('value', '') if r_final else ''
print("\nFinal modal state:", final)

ws.close()
