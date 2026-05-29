"""
cdp_drive.py — Driver CDP minimalista para conducir el Chrome del bridge (:9222).
Reutiliza el patron de src/bridge/fix_*.py (websocket + CDP) pero generico.

Uso:
  python -m src.bridge.cdp_drive nav  "https://www.tiktok.com/tiktokstudio/content"
  python -m src.bridge.cdp_drive shot "tmp_forensic/studio.png"
  python -m src.bridge.cdp_drive text                 # innerText del body
  python -m src.bridge.cdp_drive eval "document.title"
  python -m src.bridge.cdp_drive jsfile path/to.js    # ejecuta un archivo JS y devuelve el valor
"""
from __future__ import annotations
import os, sys, json, time, base64, urllib.request, websocket

CDP = "http://localhost:9222"
_ID = [0]


def _id():
    _ID[0] += 1
    return _ID[0]


def get_ws(url_filter: str = None):
    if url_filter is None:
        url_filter = os.environ.get("CDP_TAB", "tiktok")
    with urllib.request.urlopen(f"{CDP}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    pages = [t for t in tabs if t.get("type") == "page"]
    target = None
    for t in pages:
        if url_filter.lower() in t.get("url", "").lower():
            target = t
            break
    if not target and pages:
        target = pages[0]
    if not target:
        return None
    ws = websocket.WebSocket()
    ws.connect(target["webSocketDebuggerUrl"], timeout=15, origin="http://localhost:9222")
    return ws


def cdp(ws, method, params=None, wait=True):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    if not wait:
        return None
    for _ in range(400):
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid:
                return r
        except Exception:
            return None


def js(ws, expr):
    r = cdp(ws, "Runtime.evaluate",
            {"expression": expr, "returnByValue": True, "awaitPromise": True})
    res = (r or {}).get("result", {})
    if res.get("exceptionDetails"):
        return {"error": str(res["exceptionDetails"])}
    return res.get("result", {}).get("value")


def shot(ws, path):
    cdp(ws, "Page.bringToFront", {})
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        return path
    return None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("uso: nav|shot|text|eval|jsfile ...")
        return
    cmd = sys.argv[1]
    ws = get_ws()
    if not ws:
        print("[FAIL] No hay pestana en Chrome :9222")
        return
    cdp(ws, "Page.enable", {})
    cdp(ws, "Runtime.enable", {})
    if cmd == "nav":
        cdp(ws, "Page.navigate", {"url": sys.argv[2]})
        time.sleep(float(sys.argv[3]) if len(sys.argv) > 3 else 6)
        print("URL:", js(ws, "location.href"))
        print("TITLE:", js(ws, "document.title"))
    elif cmd == "shot":
        print("saved:", shot(ws, sys.argv[2]))
    elif cmd == "text":
        txt = js(ws, "document.body.innerText") or ""
        print(txt[:6000])
    elif cmd == "eval":
        print(json.dumps(js(ws, sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == "jsfile":
        with open(sys.argv[2], encoding="utf-8") as f:
            code = f.read()
        print(json.dumps(js(ws, code), ensure_ascii=False, indent=2))
    elif cmd == "click":
        needle = sys.argv[2]
        expr = ("(function(n){var els=Array.from(document.querySelectorAll("
                "'button,a,[role=button],div[role=menuitem],span,li'));"
                "var t=els.find(function(e){return (e.innerText||'').trim().toLowerCase()"
                ".includes(n.toLowerCase()) && e.offsetParent!==null;});"
                "if(t){t.click();return 'clicked: '+t.innerText.trim().slice(0,40);}"
                "return 'NOT FOUND: '+n;})(" + json.dumps(needle) + ")")
        print(js(ws, expr))
    ws.close()


if __name__ == "__main__":
    main()
