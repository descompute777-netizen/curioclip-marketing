"""
Navega Chrome via CDP WebSocket raw.
Usa el flag --remote-allow-origins=* que ahora esta en chrome_bridge.py.
python -m src.bridge.chrome_navigate --url URL [--screenshot file.png]
"""
import sys, json, time, urllib.request, base64, argparse
sys.stdout.reconfigure(encoding='utf-8')
import websocket

CDP_URL = "http://localhost:9222"
_ID = [0]


def _id():
    _ID[0] += 1
    return _ID[0]


def open_new_tab():
    req = urllib.request.Request(f"{CDP_URL}/json/new", method="PUT", data=b"")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def connect_tab(ws_url):
    ws = websocket.WebSocket()
    ws.connect(ws_url, timeout=10, origin="http://localhost:9222")
    return ws


def cdp(ws, method, params=None, wait_id=True):
    mid = _id()
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    if not wait_id:
        return None
    while True:
        try:
            r = json.loads(ws.recv())
            if r.get("id") == mid:
                return r
        except Exception:
            return None


def screenshot(ws, path):
    r = cdp(ws, "Page.captureScreenshot", {"format": "png"})
    data = (r or {}).get("result", {}).get("data", "")
    if data:
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"  Screenshot: {path}")
        return True
    return False


def get_url(ws):
    r = cdp(ws, "Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value", "")


def click_element(ws, selector):
    js = f"""
    (function() {{
        const el = document.querySelector('{selector}');
        if (el) {{ el.click(); return true; }}
        return false;
    }})()
    """
    r = cdp(ws, "Runtime.evaluate", {"expression": js, "returnByValue": True})
    return (r or {}).get("result", {}).get("result", {}).get("value", False)


def navigate_and_screenshot(url, screenshot_path="page.png", wait=4):
    print(f"\n[NAV] {url}")
    tab = open_new_tab()
    ws = connect_tab(tab["webSocketDebuggerUrl"])
    cdp(ws, "Page.navigate", {"url": url})
    time.sleep(wait)
    current = get_url(ws)
    print(f"  URL actual: {current[:100]}")
    screenshot(ws, screenshot_path)
    return ws, current


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--screenshot", default="nav_result.png")
    parser.add_argument("--wait", type=int, default=4)
    args = parser.parse_args()

    ws, current = navigate_and_screenshot(args.url, args.screenshot, args.wait)
    ws.close()
    print(f"\n[DONE] Final URL: {current}")


if __name__ == "__main__":
    main()
