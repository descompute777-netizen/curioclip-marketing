"""
Abre TikTok Developers portal en Chrome.
python -m src.bridge.open_tiktok_dev
"""
import sys, json, time, urllib.request, websocket
sys.stdout.reconfigure(encoding='utf-8')

CDP = "http://localhost:9222"
_ID = [0]

def _id(): _ID[0] += 1; return _ID[0]

def get_ws():
    with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    for t in [x for x in tabs if x.get("type") == "page"]:
        if "composio" in t.get("url", "").lower() or "dashboard" in t.get("url", "").lower():
            ws = websocket.WebSocket()
            ws.connect(t["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
            return ws
    return None

def cdp(ws, m, p=None):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid: return r
        except: return None

# Abrir nueva pestaña con TikTok Developers
req = urllib.request.Request(f"{CDP}/json/new", method="PUT", data=b"")
with urllib.request.urlopen(req, timeout=5) as r:
    new_tab = json.loads(r.read())

ws2 = websocket.WebSocket()
ws2.connect(new_tab["webSocketDebuggerUrl"], timeout=10, origin="http://localhost:9222")
cdp(ws2, "Page.navigate", {"url": "https://developers.tiktok.com/apps/"})
time.sleep(5)

url = cdp(ws2, "Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
current = (url or {}).get("result", {}).get("result", {}).get("value", "")
print(f"URL abierta: {current}")

ws2.close()

# Listar todas las pestañas
with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
    tabs = json.loads(r.read())
print("\nPestañas abiertas:")
for t in [x for x in tabs if x.get("type") == "page"]:
    print(f"  {t.get('url', '')[:80]}")
