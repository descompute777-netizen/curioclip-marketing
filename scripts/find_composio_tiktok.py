"""Encuentra el integration ID de TikTok en Composio y crea el auth config."""
import sys, json, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

KEY = 'ck_NcIb61zkczdt9WOrGTYQ'

try:
    import cloudscraper
    s = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    def get(url):
        r = s.get(url, headers={'x-api-key': KEY}, timeout=15)
        return r.status_code, r.text
    def post(url, body):
        r = s.post(url, headers={'x-api-key': KEY, 'Content-Type': 'application/json'},
                   json=body, timeout=15)
        return r.status_code, r.text
except ImportError:
    print("cloudscraper not installed")
    sys.exit(1)

BASE = 'https://backend.composio.dev'
endpoints = [
    f'{BASE}/api/v3/apps?search=tiktok',
    f'{BASE}/api/v3/apps',
    f'{BASE}/api/v3/integrations?appName=TIKTOK',
    f'{BASE}/api/v2/integrations?appName=TIKTOK',
    f'{BASE}/api/v1/integrations',
    f'{BASE}/api/v3/connectedAccounts',
    f'{BASE}/api/v3/toolkits?search=tiktok',
    f'{BASE}/api/v3/toolkit/tiktok',
    f'{BASE}/api/v1/apps/tiktok',
]

print("=== BUSCANDO TIKTOK EN COMPOSIO API ===\n")
for url in endpoints:
    try:
        code, text = get(url)
        short = url.replace(BASE, '')
        preview = text[:300]
        print(f"[{code}] {short}")
        print(f"  {preview}")
        if code == 200 and 'tiktok' in text.lower():
            print("  *** TIKTOK ENCONTRADO ***")
            try:
                data = json.loads(text)
                print(f"  FULL: {json.dumps(data, indent=2)[:500]}")
            except:
                pass
        print()
    except Exception as e:
        print(f"  ERROR: {e}\n")
