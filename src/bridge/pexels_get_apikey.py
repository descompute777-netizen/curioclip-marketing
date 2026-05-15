"""
Obtiene la API key de Pexels navegando con Chrome Bridge.
Ejecutar: python -m src.bridge.pexels_get_apikey
"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL = "http://localhost:9222"
USER_EMAIL = "descompute777@gmail.com"


def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]
        page = ctx.new_page()

        print("[NAV] Navegando a Pexels API registration...")
        page.goto("https://www.pexels.com/api/", timeout=20000)
        time.sleep(3)

        page.screenshot(path="pexels_api_page.png")
        print(f"  URL: {page.url}")
        print(f"  Title: {page.title()}")

        # Buscar boton de registro/login
        try:
            # Intentar click en "Get Started" o "Sign up"
            btn = page.locator(
                "a:has-text('Get Started'), a:has-text('Join'), button:has-text('Get Started')"
            ).first
            if btn.is_visible(timeout=3000):
                print("[CLICK] Get Started button")
                btn.click()
                time.sleep(3)
                page.screenshot(path="pexels_signup.png")
                print(f"  URL post-click: {page.url}")
        except Exception as e:
            print(f"  Botón no encontrado: {e}")

        # Si ya está logueado, ir directo al dashboard de la API
        if "pexels.com" in page.url:
            page.goto("https://www.pexels.com/api/", timeout=15000)
            time.sleep(2)

            # Buscar la API key en la página
            try:
                api_key_el = page.locator(
                    "input[readonly], code, .api-key, [data-testid='api-key']"
                ).first
                if api_key_el.is_visible(timeout=3000):
                    key = api_key_el.input_value() or api_key_el.inner_text()
                    if key and len(key) > 10:
                        print(f"\n[KEY FOUND] Pexels API Key: {key}")
                        # Guardar en .env
                        import pathlib
                        env_path = pathlib.Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env")
                        env_content = env_path.read_text(encoding='utf-8')
                        if 'PEXELS_API_KEY' not in env_content:
                            env_path.write_text(
                                env_content + f"\nPEXELS_API_KEY={key}\n",
                                encoding='utf-8'
                            )
                            print("[OK] Guardada en .env")
                        return key
            except Exception as e:
                print(f"  API key element: {e}")

        page.screenshot(path="pexels_current_state.png")
        print(f"\n[STATE] Screenshot: pexels_current_state.png")
        print(f"  URL actual: {page.url}")
        print("\nInstruccion si no se pudo automatizar:")
        print(f"  1. Ve a pexels.com/api en tu Chrome")
        print(f"  2. Registrate con Google ({USER_EMAIL})")
        print(f"  3. Copia tu API key")
        print(f"  4. Pégala en .env como: PEXELS_API_KEY=tu_key_aqui")

        page.close()


if __name__ == "__main__":
    main()
