"""Fix los 3 errores Formik en sandbox y apply changes."""
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

def keyboard_type(ws, text, mid_start):
    for char in text:
        cdp(ws, mid_start, 'Input.dispatchKeyEvent', {'type': 'char', 'text': char, 'unmodifiedText': char})
        time.sleep(0.005)

# Step 1: Find and scroll Category button into view
mid = 100
r = cdp(ws, mid, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var btns = Array.from(document.querySelectorAll('button'));
    var cat = btns.find(b => b.textContent.trim() === 'Category' && b.offsetParent !== null);
    if (cat) {
        cat.scrollIntoView({block: 'center'});
        var rect = cat.getBoundingClientRect();
        return JSON.stringify({found: true, x: rect.x + rect.width/2, y: rect.y + rect.height/2});
    }
    return JSON.stringify({found: false});
})()
"""})
val = r.get('result',{}).get('result',{}).get('value','{}') if r else '{}'
cat_info = json.loads(val)
print(f'Category button: {cat_info}')

if cat_info.get('found'):
    time.sleep(0.5)
    # Re-get coords after scroll
    mid += 1
    r2 = cdp(ws, mid, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var btns = Array.from(document.querySelectorAll('button'));
    var cat = btns.find(b => b.textContent.trim() === 'Category' && b.offsetParent !== null);
    if (!cat) return 'null';
    var rect = cat.getBoundingClientRect();
    return JSON.stringify({x: rect.x + rect.width/2, y: rect.y + rect.height/2});
})()
"""})
    coords = json.loads(r2.get('result',{}).get('result',{}).get('value','null'))
    if coords:
        print(f'Clicking Category at ({coords["x"]:.0f}, {coords["y"]:.0f})')
        mid += 1
        cdp(ws, mid, 'Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': coords['x'], 'y': coords['y'], 'button': 'left', 'clickCount': 1})
        mid += 1
        cdp(ws, mid, 'Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': coords['x'], 'y': coords['y'], 'button': 'left', 'clickCount': 1})
        time.sleep(2)

        # Select Social Networking
        mid += 1
        r3 = cdp(ws, mid, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var opts = Array.from(document.querySelectorAll('[role=option]'));
    var sn = opts.find(o => o.textContent.trim() === 'Social Networking' && o.offsetParent !== null);
    if (sn) {
        sn.scrollIntoView({block: 'center'});
        var rect = sn.getBoundingClientRect();
        return JSON.stringify({found: true, x: rect.x + rect.width/2, y: rect.y + rect.height/2});
    }
    return JSON.stringify({found: false, totalOpts: opts.length, visibleOpts: opts.filter(o=>o.offsetParent!==null).map(o=>o.textContent.trim().substring(0,30)).slice(0,15)});
})()
"""})
        sn_info = json.loads(r3.get('result',{}).get('result',{}).get('value','{}'))
        print(f'Social Networking option: {sn_info}')

        if sn_info.get('found'):
            mid += 1
            cdp(ws, mid, 'Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': sn_info['x'], 'y': sn_info['y'], 'button': 'left', 'clickCount': 1})
            mid += 1
            cdp(ws, mid, 'Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': sn_info['x'], 'y': sn_info['y'], 'button': 'left', 'clickCount': 1})
            print('Selected Social Networking')

time.sleep(2)

# Step 2: Fill Description textarea
mid += 10
r4 = cdp(ws, mid, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var tas = Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent !== null);
    var desc = tas.find(t => {
        // Find textarea whose label contains 'Description'
        if (t.id) {
            var lbl = document.querySelector('label[for=\"'+t.id+'\"]');
            if (lbl && lbl.textContent.includes('Description')) return true;
        }
        return false;
    }) || tas[0];
    if (desc) {
        desc.scrollIntoView({block: 'center'});
        var rect = desc.getBoundingClientRect();
        return JSON.stringify({found: true, x: rect.x + 30, y: rect.y + 30, label: desc.id ? (document.querySelector('label[for=\"'+desc.id+'\"]')?.textContent.trim() || '') : ''});
    }
    return JSON.stringify({found: false});
})()
"""})
desc_info = json.loads(r4.get('result',{}).get('result',{}).get('value','{}'))
print(f'Description textarea: {desc_info}')

if desc_info.get('found'):
    time.sleep(0.8)
    mid += 1
    r5 = cdp(ws, mid, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var tas = Array.from(document.querySelectorAll('textarea')).filter(t => t.offsetParent !== null);
    var desc = tas.find(t => {
        if (t.id) {
            var lbl = document.querySelector('label[for=\"'+t.id+'\"]');
            if (lbl && lbl.textContent.includes('Description')) return true;
        }
        return false;
    }) || tas[0];
    if (!desc) return 'null';
    var rect = desc.getBoundingClientRect();
    return JSON.stringify({x: rect.x + 30, y: rect.y + 30});
})()
"""})
    desc_coords = json.loads(r5.get('result',{}).get('result',{}).get('value','null'))
    if desc_coords:
        print(f'Clicking description at ({desc_coords["x"]:.0f}, {desc_coords["y"]:.0f})')
        mid += 1
        cdp(ws, mid, 'Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': desc_coords['x'], 'y': desc_coords['y'], 'button': 'left', 'clickCount': 1})
        mid += 1
        cdp(ws, mid, 'Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': desc_coords['x'], 'y': desc_coords['y'], 'button': 'left', 'clickCount': 1})
        time.sleep(0.5)
        text = 'CurioClip plataforma marketing digital publicacion automatizada contenido viral TikTok'
        mid += 1
        keyboard_type(ws, text, mid)
        print(f'Typed {len(text)} chars')

time.sleep(2)

# Click elsewhere to blur
mid += 100
cdp(ws, mid, 'Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': 50, 'y': 50, 'button': 'left', 'clickCount': 1})
mid += 1
cdp(ws, mid, 'Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': 50, 'y': 50, 'button': 'left', 'clickCount': 1})
time.sleep(1)

# Click Apply changes
mid += 10
r6 = cdp(ws, mid, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
(function(){
    var btns = Array.from(document.querySelectorAll('button'));
    var apply = btns.find(b => b.textContent.trim() === 'Apply changes' && b.offsetParent !== null);
    if (apply) { apply.scrollIntoView({block:'center'}); apply.click(); return 'clicked'; }
    return 'not found';
})()
"""})
print(f'Apply changes: {r6.get("result",{}).get("result",{}).get("value","") if r6 else ""}')

time.sleep(5)

# Final state
mid += 10
r7 = cdp(ws, mid, 'Runtime.evaluate', {'returnByValue': True, 'expression': """
JSON.stringify({
    errCount: (document.body.innerText.match(/has (\\d+) error/) || ['none','?'])[1],
    iconErr: document.body.innerText.includes('App icon is required'),
    catErr: document.body.innerText.includes('Please select a category'),
    descErr: document.body.innerText.includes('Please fill out the required field'),
    successMsg: document.body.innerText.includes('Changes applied') || document.body.innerText.includes('Successfully saved')
})
"""})
print(f'Final state: {r7.get("result",{}).get("result",{}).get("value","") if r7 else ""}')

ws.close()
