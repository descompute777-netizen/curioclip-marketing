"""Final fix: Description via React setter + Category via custom dropdown."""
import websocket, json, urllib.request, time, sys
sys.stdout.reconfigure(encoding='utf-8')

tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
sandbox_tab = next(t for t in tabs if '/sandbox/' in t.get('url',''))
ws = websocket.create_connection(sandbox_tab['webSocketDebuggerUrl'], timeout=20)
ws.settimeout(10)

def cdp(ws, mid, method, params=None):
    msg = {'id': mid, 'method': method}
    if params: msg['params'] = params
    ws.send(json.dumps(msg))
    for _ in range(50):
        try:
            r = json.loads(ws.recv())
            if r.get('id') == mid: return r
        except: break
    return None

# Step 1: Fill description via React-compatible setter (worked for URL inputs)
r = cdp(ws, 1, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var tas = Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent !== null);
    var desc = tas.find(t => {
        if (t.id) {
            var lbl = document.querySelector('label[for="'+t.id+'"]');
            if (lbl && lbl.textContent.includes('Description')) return true;
        }
        return false;
    });
    if (!desc) return JSON.stringify({found: false, totalTAs: tas.length});

    var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
    setter.call(desc, 'CurioClip plataforma de marketing digital para publicacion automatizada de contenido viral en TikTok y Facebook con curiosidades cientificas, datos asombrosos y entretenimiento educativo para audiencia hispanohablante de 13 a 35 anios.');
    desc.dispatchEvent(new Event('input', {bubbles: true}));
    desc.dispatchEvent(new Event('change', {bubbles: true}));
    desc.dispatchEvent(new Event('blur', {bubbles: true}));
    return JSON.stringify({set: true, value: desc.value.substring(0, 80)});
})()
"""})
print(f'Description set: {r.get("result",{}).get("result",{}).get("value","") if r else ""}')

time.sleep(1)

# Step 2: Find Category trigger - it might be div, combobox, or special select
r2 = cdp(ws, 2, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    // Find all elements containing 'Category *' as direct text and look for siblings/children
    var allEls = Array.from(document.querySelectorAll('*')).filter(el => el.children.length < 5);
    var catLabels = allEls.filter(el => el.textContent.trim() === 'Category *' || el.textContent.trim() === 'Category');

    var results = [];
    catLabels.forEach(lbl => {
        // Look at next siblings or parent's children
        var parent = lbl.parentElement;
        if (parent) {
            // Look for clickable triggers
            var siblings = Array.from(parent.querySelectorAll('*')).filter(e =>
                e !== lbl && e.offsetParent !== null &&
                (e.tagName === 'BUTTON' || e.getAttribute('role') === 'combobox' || e.getAttribute('role') === 'button' ||
                 e.tabIndex >= 0 || (e.className && e.className.includes && e.className.includes('select')) ||
                 e.tagName === 'DIV' && e.children.length < 3)
            );
            siblings.forEach(s => {
                var rect = s.getBoundingClientRect();
                if (rect.width > 50 && rect.height > 10 && rect.height < 100) {
                    results.push({
                        tag: s.tagName, role: s.getAttribute('role'), text: s.textContent.trim().substring(0, 40),
                        x: rect.x + rect.width/2, y: rect.y + rect.height/2,
                        className: (s.className || '').substring(0, 50)
                    });
                }
            });
        }
    });
    return JSON.stringify(results.slice(0, 10));
})()
"""})
cat_candidates = json.loads(r2.get('result',{}).get('result',{}).get('value','[]') if r2 else '[]')
print(f'\nCategory candidates ({len(cat_candidates)}):')
for c in cat_candidates[:8]:
    print(f'  {c["tag"]}[{c.get("role","")}]: "{c["text"][:30]}" at ({c["x"]:.0f},{c["y"]:.0f})')

# Try clicking the most likely category trigger (a div containing Category that has minimal text)
r3 = cdp(ws, 3, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    // Look specifically for the Category dropdown - in TUX (TikTok UX) it's usually a button
    // Try to find by data-e2e attribute
    var sels = Array.from(document.querySelectorAll('[data-e2e*="select"], [data-e2e*="Select"], [data-e2e*="dropdown"], [data-e2e*="Category"]'));
    if (sels.length > 0) {
        var first = sels.find(s => s.offsetParent !== null);
        if (first) {
            first.scrollIntoView({block: 'center'});
            var rect = first.getBoundingClientRect();
            return JSON.stringify({found: true, via: 'data-e2e', text: first.textContent.trim().substring(0,30), x: rect.x + rect.width/2, y: rect.y + rect.height/2, tag: first.tagName});
        }
    }
    // Try to find by looking near 'Category' text for a clickable element
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    var node;
    while (node = walker.nextNode()) {
        if (node.textContent.trim() === 'Category *') {
            var parent = node.parentElement;
            // Look at grand-parent's children
            for (var depth = 0; depth < 3; depth++) {
                parent = parent.parentElement;
                if (!parent) break;
                // Find any interactive element
                var clickables = Array.from(parent.querySelectorAll('*')).filter(e =>
                    e.tagName === 'BUTTON' || e.getAttribute('role') || e.tabIndex >= 0
                );
                for (var c of clickables) {
                    if (c.textContent.trim().toLowerCase().includes('select')) {
                        c.scrollIntoView({block:'center'});
                        var rect = c.getBoundingClientRect();
                        return JSON.stringify({found: true, via: 'select_text', text: c.textContent.trim().substring(0,30), x: rect.x + rect.width/2, y: rect.y + rect.height/2});
                    }
                }
            }
        }
    }
    return JSON.stringify({found: false});
})()
"""})
val = r3.get('result',{}).get('result',{}).get('value','{}') if r3 else '{}'
cat_trigger = json.loads(val)
print(f'\nCategory trigger: {cat_trigger}')

if cat_trigger.get('found'):
    time.sleep(0.5)
    # Re-get coords after scroll
    r3b = cdp(ws, 4, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var sels = Array.from(document.querySelectorAll('[data-e2e*="select"], [data-e2e*="Select"]'));
    var first = sels.find(s => s.offsetParent !== null && (s.textContent.trim() === 'Select' || s.textContent.trim().toLowerCase().includes('select')));
    if (first) {
        var rect = first.getBoundingClientRect();
        return JSON.stringify({x: rect.x + rect.width/2, y: rect.y + rect.height/2});
    }
    return 'null';
})()
"""})
    fresh = json.loads(r3b.get('result',{}).get('result',{}).get('value','null'))
    if fresh:
        cdp(ws, 5, 'Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': fresh['x'], 'y': fresh['y'], 'button': 'left', 'clickCount': 1})
        cdp(ws, 6, 'Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': fresh['x'], 'y': fresh['y'], 'button': 'left', 'clickCount': 1})
        print(f'Clicked Category trigger at ({fresh["x"]:.0f}, {fresh["y"]:.0f})')
        time.sleep(2)

        # Select Social Networking option
        r4 = cdp(ws, 7, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var opts = Array.from(document.querySelectorAll('[role=option]'));
    var sn = opts.find(o => o.textContent.trim() === 'Social Networking' && o.offsetParent !== null);
    if (sn) {
        sn.scrollIntoView({block: 'center'});
        var rect = sn.getBoundingClientRect();
        sn.click();
        return JSON.stringify({clicked: true, text: sn.textContent.trim()});
    }
    return JSON.stringify({clicked: false, options: opts.filter(o=>o.offsetParent!==null).map(o=>o.textContent.trim()).slice(0,15)});
})()
"""})
        print(f'Social Networking: {r4.get("result",{}).get("result",{}).get("value","") if r4 else ""}')

time.sleep(2)

# Click somewhere to blur
cdp(ws, 100, 'Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': 50, 'y': 50, 'button': 'left', 'clickCount': 1})
cdp(ws, 101, 'Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': 50, 'y': 50, 'button': 'left', 'clickCount': 1})
time.sleep(1)

# Click Apply changes
r5 = cdp(ws, 200, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var btns = Array.from(document.querySelectorAll('button'));
    var apply = btns.find(b => b.textContent.trim() === 'Apply changes' && b.offsetParent !== null);
    if (apply) { apply.scrollIntoView({block:'center'}); apply.click(); return 'clicked'; }
    return 'not found';
})()
"""})
print(f'\nApply changes: {r5.get("result",{}).get("result",{}).get("value","") if r5 else ""}')

time.sleep(5)

# Final state
r6 = cdp(ws, 300, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
JSON.stringify({
    errCount: (document.body.innerText.match(/has (\\d+) error/) || ['none','?'])[1],
    catErr: document.body.innerText.includes('Please select a category'),
    descErr: document.body.innerText.includes('Please fill out the required field'),
    iconErr: document.body.innerText.includes('App icon is required')
})
"""})
print(f'\nFinal state: {r6.get("result",{}).get("result",{}).get("value","") if r6 else ""}')

ws.close()
