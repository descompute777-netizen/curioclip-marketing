"""Prueba sistemática de la API de Composio con diferentes headers y endpoints."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

KEY = 'ck_NcIb61zkczdt9WOrGTYQ'

try:
    import cloudscraper
    s = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
except ImportError:
    print("cloudscraper not installed"); sys.exit(1)

BASE = 'https://backend.composio.dev'

# Diferentes variantes de header
header_variants = [
    {'x-api-key': KEY},
    {'x-composio-api-key': KEY},
    {'Authorization': f'Bearer {KEY}'},
    {'Authorization': f'Api-Key {KEY}'},
    {'x-api-key': KEY, 'Content-Type': 'application/json'},
]

# Endpoints que podrían funcionar
test_endpoints = [
    '/api/v3/toolkits',
    '/api/v3/connections',
    '/api/v3/auth_configs',
    '/api/v3/authConfigs',
    '/api/v3/auth-configs',
    '/api/v3/connected_accounts',
    '/api/v3/entity',
    '/api/v3/entity/default',
]

print("=== HEADER VARIANTS TEST con /api/v3/toolkits ===\n")
for headers in header_variants:
    try:
        r = s.get(f'{BASE}/api/v3/toolkits', headers=headers, timeout=10)
        print(f"[{r.status_code}] headers={list(headers.keys())}: {r.text[:150]}")
    except Exception as e:
        print(f"ERROR: {e}")

print("\n=== ENDPOINT VARIANTS con x-api-key ===\n")
for ep in test_endpoints:
    try:
        r = s.get(f'{BASE}{ep}', headers={'x-api-key': KEY}, timeout=10)
        print(f"[{r.status_code}] {ep}: {r.text[:200]}")
    except Exception as e:
        print(f"ERROR {ep}: {e}")
