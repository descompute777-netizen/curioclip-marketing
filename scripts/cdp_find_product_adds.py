"""Identifica y clickea los botones Add de Login Kit y Content Posting API."""
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

# Strategy: Find the modal overlay with Add Products title
# Then find all "Add" buttons within that overlay with their NEAREST product title
r = cdp_cmd(ws, 1, 'Runtime.evaluate', {
    'expression': r'''
(function() {
    var results = [];

    // Find the Add products overlay
    var allEls = document.querySelectorAll('[class*="Overlay"], [class*="overlay"], [role="dialog"]');
    var modal = null;
    for (var i = 0; i < allEls.length; i++) {
        if (allEls[i].textContent.includes("Login Kit") && allEls[i].textContent.includes("Share Kit")) {
            modal = allEls[i];
            break;
        }
    }

    if (!modal) {
        // Try getting all divs that contain the product list
        var allDivs = document.querySelectorAll("div");
        for (var i = 0; i < allDivs.length; i++) {
            var t = allDivs[i].textContent;
            if (t.includes("Login Kit") && t.includes("Content Posting") && allDivs[i].children.length > 1) {
                // Take the SMALLEST element that still contains both
                if (!modal || allDivs[i].textContent.length < modal.textContent.length) {
                    modal = allDivs[i];
                }
            }
        }
    }

    if (!modal) return "MODAL NOT FOUND";

    // Find all button-like elements inside the modal
    var btns = modal.querySelectorAll("button");
    btns.forEach(function(btn, i) {
        var t = btn.textContent.trim();
        // Get the section title (look for h1/h2/h3/strong near this button)
        var row = btn.closest('[class*="product"], [class*="Product"], [class*="item"], [class*="card"]');
        var rowTitle = row ? row.querySelector('h1,h2,h3,h4,strong,b,[class*="title"],[class*="name"]') : null;
        var title = rowTitle ? rowTitle.textContent.trim() : "?";
        // Also check previous siblings
        var prevSib = btn.parentElement;
        var sibText = prevSib ? prevSib.previousElementSibling ? prevSib.previousElementSibling.textContent.trim().substring(0,50) : "" : "";
        results.push("btn" + i + "|text=" + t + "|title=" + title + "|prev=" + sibText);
    });

    return results.join("\n") || "No buttons in modal";
})()
''',
    'returnByValue': True
})
val = r.get('result', {}).get('result', {}).get('value', '') if r else 'ERROR'
with open('tiktok_modal_buttons.txt', 'w', encoding='utf-8') as f:
    f.write(val)
print(val[:3000])

ws.close()
