"""Configura PEXELS_API_KEY en GitHub Secrets."""
import sys, json, base64, subprocess
sys.stdout.reconfigure(encoding='utf-8')

REPO = "descompute777-netizen/curioclip-marketing"
PEXELS_KEY = "k0iMZlUKh9p7jpNUKjRQQ4eCPcXQ7YW4ufpBkEoZOCbKuDOt9x3xVqjR"

proc = subprocess.Popen(['git','credential','fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, _ = proc.communicate(input=b'protocol=https\nhost=github.com\n\n', timeout=5)
GH_TOKEN = next((l.split('=',1)[1] for l in out.decode(errors='ignore').splitlines() if l.startswith('password=')), '')

if not GH_TOKEN:
    print("ERROR: no GitHub token"); sys.exit(1)
print(f"Token OK ({len(GH_TOKEN)} chars)")

def get_pub_key():
    req = __import__('urllib.request', fromlist=['Request','urlopen']).Request(
        f'https://api.github.com/repos/{REPO}/actions/secrets/public-key',
        headers={'Authorization': f'Bearer {GH_TOKEN}', 'Accept': 'application/vnd.github+json'})
    with __import__('urllib.request', fromlist=['urlopen']).urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def encrypt(pub_b64, value):
    try:
        from nacl.public import PublicKey, SealedBox
        box = SealedBox(PublicKey(base64.b64decode(pub_b64)))
        return base64.b64encode(box.encrypt(value.encode())).decode()
    except ImportError:
        subprocess.run([sys.executable,'-m','pip','install','PyNaCl','-q'], check=True)
        from nacl.public import PublicKey, SealedBox
        box = SealedBox(PublicKey(base64.b64decode(pub_b64)))
        return base64.b64encode(box.encrypt(value.encode())).decode()

def set_secret(name, value, key_id, enc_value):
    payload = json.dumps({'encrypted_value': enc_value, 'key_id': key_id}).encode()
    req = __import__('urllib.request', fromlist=['Request','urlopen']).Request(
        f'https://api.github.com/repos/{REPO}/actions/secrets/{name}',
        data=payload,
        headers={'Authorization': f'Bearer {GH_TOKEN}', 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'},
        method='PUT')
    try:
        with __import__('urllib.request', fromlist=['urlopen']).urlopen(req, timeout=10) as r:
            return r.status in (201, 204)
    except __import__('urllib.error').HTTPError as e:
        return e.code in (201, 204)

pk_data = get_pub_key()
key_id, pub_key = pk_data['key_id'], pk_data['key']
print(f"Public key OK: {key_id}")

enc = encrypt(pub_key, PEXELS_KEY)
ok = set_secret('PEXELS_API_KEY', PEXELS_KEY, key_id, enc)
print(f"PEXELS_API_KEY en GitHub Secrets: {'OK' if ok else 'FAIL'}")
