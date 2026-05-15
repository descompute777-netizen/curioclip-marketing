"""
Completa OAuth TikTok en Composio usando CDP raw (sin Playwright).
Usa websocket-client para comunicarse directamente con Chrome.
"""
import sys, json, time, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

import websocket

CDP_URL = "http://localhost:9222"
COMPOSIO_KEY = "ck_NcIb61zkczdt9WOrGTYQ"
MSG_ID = [0]


def next_id():
    MSG_ID[0] += 1
    return MSG_ID[0]


def cdp_send(ws, method, params=None):
    msg = {"id": next_id(), "method": method, "params": params or {}}
    ws.send(json.dumps(msg))
    # Leer respuestas hasta encontrar la del ID correcto
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == msg["id"]:
            return data
        # Ignorar eventos (sin id) y respuestas de otros comandos


def get_tab_ws_url():
    """Obtiene la WebSocket URL de la primera pestaña de Chrome."""
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=5) as r:
        tabs = json.loads(r.read())
    pages = [t for t in tabs if t.get("type") == "page"]
    if not pages:
        raise RuntimeError("No hay pestañas abiertas en Chrome")
    return pages[0]["webSocketDebuggerUrl"]


def open_new_tab_ws():
    """Abre una nueva pestaña y retorna su WebSocket URL."""
    with urllib.request.urlopen(
        urllib.request.Request(f"{CDP_URL}/json/new", method="PUT"), timeout=5
    ) as r:
        tab = json.loads(r.read())
    return tab["webSocketDebuggerUrl"]


def eval_js(ws, js_code, timeout=15):
    """Evalúa JavaScript y retorna el resultado."""
    resp = cdp_send(ws, "Runtime.evaluate", {
        "expression": js_code,
        "awaitPromise": True,
        "returnByValue": True,
        "timeout": timeout * 1000
    })
    result = resp.get("result", {}).get("result", {})
    if result.get("type") == "string":
        return result.get("value", "")
    elif result.get("type") == "object":
        return result.get("value", {})
    return result.get("value", str(result))


def navigate(ws, url):
    resp = cdp_send(ws, "Page.navigate", {"url": url})
    time.sleep(2)
    return resp


def main():
    print("[CDP] Conectando a Chrome via WebSocket...")

    # Intentar primero con cloudscraper (más fácil, evita Cloudflare)
    print("\n[ATTEMPT 1] Composio API via cloudscraper...")
    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
        resp = scraper.post(
            "https://backend.composio.dev/api/v1/connectedAccounts",
            headers={"x-api-key": COMPOSIO_KEY, "Content-Type": "application/json"},
            json={"integrationId": "TIKTOK", "entityId": "default"},
            timeout=15
        )
        print(f"  Status: {resp.status_code}")
        body = resp.text
        print(f"  Response: {body[:300]}")

        try:
            data = json.loads(body)
            redirect_url = data.get("redirectUrl", "")
            if redirect_url:
                print(f"  REDIRECT URL: {redirect_url}")
                # Abrir URL en Chrome vía CDP WebSocket
                ws_url = open_new_tab_ws()
                ws = websocket.WebSocket()
                ws.connect(ws_url, timeout=10)
                print(f"\n[CDP] Navegando a OAuth URL...")
                navigate(ws, redirect_url)
                time.sleep(5)

                current_url_result = eval_js(ws, "window.location.href")
                print(f"  URL actual: {current_url_result}")

                # Tomar screenshot via CDP
                ss = cdp_send(ws, "Page.captureScreenshot", {"format": "png"})
                import base64
                if "result" in ss and "data" in ss["result"]:
                    with open("composio_oauth.png", "wb") as f:
                        f.write(base64.b64decode(ss["result"]["data"]))
                    print("  Screenshot: composio_oauth.png")

                ws.close()
                return redirect_url
        except json.JSONDecodeError:
            print(f"  JSON parse error: {body[:100]}")

    except Exception as e:
        print(f"  cloudscraper error: {e}")

    print("\n[ATTEMPT 2] Composio API via Chrome JS execution...")
    try:
        ws_url = open_new_tab_ws()
        ws = websocket.WebSocket()
        ws.connect(ws_url, timeout=10)

        # Navegar a blank para tener contexto limpio
        navigate(ws, "about:blank")

        # Ejecutar el fetch desde dentro de Chrome
        js_fetch = f"""
(async () => {{
    try {{
        const r = await fetch('https://backend.composio.dev/api/v1/connectedAccounts', {{
            method: 'POST',
            headers: {{
                'x-api-key': '{COMPOSIO_KEY}',
                'Content-Type': 'application/json',
                'Origin': 'https://app.composio.dev',
                'Referer': 'https://app.composio.dev/'
            }},
            body: JSON.stringify({{integrationId: 'TIKTOK', entityId: 'default'}})
        }});
        const text = await r.text();
        return JSON.stringify({{status: r.status, body: text}});
    }} catch(e) {{
        return JSON.stringify({{error: e.message}});
    }}
}})()
"""
        result_str = eval_js(ws, js_fetch, timeout=20)
        print(f"  JS result: {result_str[:400] if result_str else '(empty)'}")

        if result_str:
            try:
                outer = json.loads(result_str)
                body = outer.get("body", "")
                if body:
                    inner = json.loads(body)
                    redirect_url = inner.get("redirectUrl", "")
                    if redirect_url:
                        print(f"\n  REDIRECT URL: {redirect_url}")
                        navigate(ws, redirect_url)
                        time.sleep(5)
                        current = eval_js(ws, "window.location.href")
                        print(f"  URL post-nav: {current}")
                        ws.close()
                        return redirect_url
            except Exception as e:
                print(f"  Parse: {e}")

        # Fallback: navegar directo a app.composio.dev
        print("\n[FALLBACK] Navegando a app.composio.dev/apps/tiktok...")
        navigate(ws, "https://app.composio.dev/apps/tiktok")
        time.sleep(5)

        current = eval_js(ws, "window.location.href")
        print(f"  URL: {current}")

        ss = cdp_send(ws, "Page.captureScreenshot", {"format": "png"})
        if "result" in ss and "data" in ss["result"]:
            import base64
            with open("composio_app_page.png", "wb") as f:
                f.write(base64.b64decode(ss["result"]["data"]))
            print("  Screenshot: composio_app_page.png")

        ws.close()

    except Exception as e:
        print(f"  CDP error: {e}")
        import traceback
        traceback.print_exc()

    print("\n[INFO] Ver screenshots para estado actual del OAuth.")


if __name__ == "__main__":
    main()
