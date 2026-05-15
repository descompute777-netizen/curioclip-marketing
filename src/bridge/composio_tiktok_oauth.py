"""
Completa el OAuth de TikTok en Composio via Chrome Bridge.
Ejecutar: python -m src.bridge.composio_tiktok_oauth
"""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')

COMPOSIO_API_KEY = "ck_NcIb61zkczdt9WOrGTYQ"
CDP_URL = "http://localhost:9222"

JS_CALL = """
async () => {
    try {
        const r = await fetch('https://backend.composio.dev/api/v1/connectedAccounts', {
            method: 'POST',
            headers: {
                'x-api-key': '""" + COMPOSIO_API_KEY + """',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({integrationId: 'TIKTOK', entityId: 'default'})
        });
        const text = await r.text();
        return {status: r.status, body: text};
    } catch(e) {
        return {error: e.message};
    }
}
"""

JS_CHECK = """
async () => {
    try {
        const r = await fetch('https://backend.composio.dev/api/v1/connectedAccounts', {
            method: 'GET',
            headers: {'x-api-key': '""" + COMPOSIO_API_KEY + """'}
        });
        const text = await r.text();
        return {status: r.status, body: text};
    } catch(e) {
        return {error: e.message};
    }
}
"""


def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]
        page = ctx.new_page()

        print("[STEP 1] Verificando cuentas conectadas en Composio...")
        page.goto("about:blank")
        check = page.evaluate(JS_CHECK)
        print(f"  Status: {check.get('status')}")

        body_check = check.get('body', '')
        try:
            data_check = json.loads(body_check)
            items = data_check.get('items', [])
            tiktok_connected = any(
                'tiktok' in str(item.get('appName', '')).lower() or
                'tiktok' in str(item.get('integrationId', '')).lower()
                for item in items
            )
            print(f"  Cuentas conectadas: {len(items)}")
            print(f"  TikTok ya conectado: {tiktok_connected}")

            if tiktok_connected:
                print("[OK] TikTok ya esta conectado a Composio. No se necesita OAuth.")
                page.close()
                return
        except Exception as e:
            print(f"  Parse error: {e} | Raw: {body_check[:200]}")

        print("\n[STEP 2] Iniciando conexion TikTok en Composio...")
        result = page.evaluate(JS_CALL)
        status = result.get('status')
        body = result.get('body', result.get('error', ''))
        print(f"  Status: {status}")

        redirect_url = ""
        try:
            data = json.loads(body)
            redirect_url = data.get('redirectUrl', '') or data.get('connectionStatus', '')
            connection_id = data.get('id', '')
            print(f"  Connection ID: {connection_id}")
            print(f"  Redirect URL: {redirect_url[:100] if redirect_url else '(none)'}")
        except Exception as e:
            print(f"  Parse error: {e}")
            print(f"  Body: {body[:300]}")

        if redirect_url and redirect_url.startswith('http'):
            print(f"\n[STEP 3] Navegando a OAuth TikTok: {redirect_url[:80]}...")
            page.goto(redirect_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(3)

            current_url = page.url
            print(f"  URL actual: {current_url[:100]}")

            screenshot_path = "composio_oauth_state.png"
            page.screenshot(path=screenshot_path)
            print(f"  Screenshot: {screenshot_path}")

            # Detectar si ya llegamos al callback de Composio (OAuth completado)
            if "composio" in current_url and "callback" in current_url.lower():
                print("[OK] OAuth completado automaticamente!")
            elif "tiktok.com" in current_url:
                print("[INFO] En pagina de TikTok. Verificando si ya hay sesion activa...")
                time.sleep(5)
                # Si TikTok ya esta logueado, puede completar solo
                try:
                    # Buscar boton de autorizar
                    auth_btn = page.locator("button:has-text('Authorize'), button:has-text('Confirm')").first
                    if auth_btn.is_visible(timeout=3000):
                        auth_btn.click()
                        print("[CLICK] Boton de autorizacion clickeado")
                        time.sleep(5)
                        page.screenshot(path="composio_after_auth.png")
                except Exception as e:
                    print(f"  Auto-auth: {e}")
            else:
                print(f"[INFO] En: {current_url[:100]}")
                print("  El OAuth puede requerir login manual en Composio.")
                print("  Abre esta URL en tu Chrome y completa el proceso:")
                print(f"  {redirect_url}")
        else:
            print(f"\n[FALLBACK] Sin redirect URL automatica.")
            print("  Navegando directamente a Composio...")
            page.goto("https://app.composio.dev/apps/tiktok", timeout=15000)
            time.sleep(3)
            page.screenshot(path="composio_tiktok_page.png")
            print(f"  Screenshot guardado: composio_tiktok_page.png")
            print(f"  URL: {page.url}")

        page.close()
        print("\n[DONE] Proceso de OAuth TikTok completado o en progreso.")


if __name__ == "__main__":
    main()
