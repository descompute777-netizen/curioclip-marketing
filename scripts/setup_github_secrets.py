"""
Configurador de GitHub Secrets — CurioClip
==========================================
Configura automáticamente todos los secrets necesarios en GitHub.

Uso:
  python scripts/setup_github_secrets.py --token TU_PAT_TOKEN

Cómo obtener el PAT (Personal Access Token):
  1. Ve a: https://github.com/settings/tokens/new
  2. Nombre: "CurioClip Secrets Manager"
  3. Expiration: 90 days
  4. Scopes: selecciona SOLO "repo" (incluye secrets)
  5. Generate token → copiar

Después de correr este script, el PAT ya no se necesita.
"""
import sys, os, json, base64, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = "descompute777-netizen/curioclip-marketing"


def load_env_secrets() -> dict:
    """Lee los secrets del .env local."""
    env_path = ROOT / ".env"
    secrets = {}
    if not env_path.exists():
        print("[WARN] .env no encontrado.")
        return secrets

    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and "<<<PENDIENTE>>>" not in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if value and key in [
                "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "COMPOSIO_API_KEY",
                "VISUALEYES_API_KEY", "PEXELS_API_KEY", "META_PAGE_ACCESS_TOKEN"
            ]:
                secrets[key] = value

    return secrets


def get_repo_public_key(token: str) -> tuple[str, str]:
    """Obtiene la clave pública del repo para encriptar secrets."""
    result = subprocess.run([
        "curl", "-s",
        f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/vnd.github+json"
    ], capture_output=True, text=True, timeout=15)

    data = json.loads(result.stdout)
    return data.get("key_id", ""), data.get("key", "")


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    """Encripta el secret con la clave pública del repo (libsodium/nacl)."""
    try:
        from nacl import encoding, public as nacl_public
        pk_bytes = base64.b64decode(public_key_b64)
        pub_key = nacl_public.PublicKey(pk_bytes)
        sealed_box = nacl_public.SealedBox(pub_key)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "PyNaCl", "-q"], check=True)
        from nacl import encoding, public as nacl_public
        pk_bytes = base64.b64decode(public_key_b64)
        pub_key = nacl_public.PublicKey(pk_bytes)
        sealed_box = nacl_public.SealedBox(pub_key)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")


def set_secret(token: str, key_id: str, secret_name: str,
               encrypted_value: str) -> bool:
    """Envía el secret encriptado a GitHub API."""
    payload = json.dumps({"encrypted_value": encrypted_value, "key_id": key_id})
    result = subprocess.run([
        "curl", "-s", "-X", "PUT",
        f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/vnd.github+json",
        "-H", "Content-Type: application/json",
        "-d", payload
    ], capture_output=True, text=True, timeout=15)
    return result.returncode == 0 and result.stdout.strip() in ("", "{}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Configura GitHub Secrets para CurioClip")
    parser.add_argument("--token", required=True, help="GitHub PAT con permisos repo")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se configuraría")
    args = parser.parse_args()

    token = args.token
    secrets = load_env_secrets()

    if not secrets:
        print("[ERROR] No se encontraron secrets válidos en .env")
        sys.exit(1)

    print(f"\nSecrets a configurar en {REPO}:")
    for k, v in secrets.items():
        masked = v[:8] + "..." + v[-4:]
        print(f"  {k}: {masked}")

    if args.dry_run:
        print("\n[DRY RUN] No se configuraron secrets. Quitar --dry-run para ejecutar.")
        return

    print(f"\nObteniendo clave pública del repo...")
    key_id, public_key = get_repo_public_key(token)
    if not key_id:
        print("[ERROR] No se pudo obtener la clave pública. Verifica el token.")
        sys.exit(1)
    print(f"[OK] key_id: {key_id}")

    configured = 0
    for secret_name, secret_value in secrets.items():
        encrypted = encrypt_secret(public_key, secret_value)
        if set_secret(token, key_id, secret_name, encrypted):
            print(f"  [OK] {secret_name} ✓")
            configured += 1
        else:
            print(f"  [FAIL] {secret_name} — verificar permisos del token")

    print(f"\n[DONE] {configured}/{len(secrets)} secrets configurados.")
    print("\nPróximo paso: conectar TikTok en Composio (ver SETUP.md)")


if __name__ == "__main__":
    main()
