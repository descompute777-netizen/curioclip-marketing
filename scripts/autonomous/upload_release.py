"""
GitHub Release Uploader — Videos CurioClip
============================================
Sube videos producidos a GitHub Releases para obtener URLs públicas.
Esas URLs son las que usa Composio (TIKTOK_PUBLISH_VIDEO) para publicar.

Usa la GitHub API v3 vía curl (disponible en GitHub Actions Ubuntu).
No requiere gh CLI instalado.
"""
import os, sys, json, subprocess, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
SPRINT_N = ((datetime.date.today() - datetime.date(2026, 5, 6)).days // 7) + 1
TODAY = datetime.date.today().isoformat()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = "descompute777-netizen/curioclip-marketing"
RELEASE_TAG = f"sprint-{SPRINT_N}-{TODAY}"


def create_github_release() -> str | None:
    """Crea un GitHub Release y retorna su upload_url."""
    if not GITHUB_TOKEN:
        print("[SKIP] GITHUB_TOKEN no disponible.")
        return None

    payload = json.dumps({
        "tag_name": RELEASE_TAG,
        "name": f"CurioClip Sprint {SPRINT_N} — {TODAY}",
        "body": f"Videos producidos automáticamente para Sprint {SPRINT_N}.",
        "draft": False,
        "prerelease": False
    })

    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://api.github.com/repos/{GITHUB_REPO}/releases",
        "-H", f"Authorization: Bearer {GITHUB_TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", payload
    ], capture_output=True, text=True, timeout=30)

    try:
        data = json.loads(result.stdout)
        upload_url = data.get("upload_url", "").replace("{?name,label}", "")
        release_id = data.get("id")
        if upload_url:
            print(f"[OK] Release creado: {RELEASE_TAG} (id={release_id})")
            return upload_url
        print(f"[WARN] Release response: {result.stdout[:200]}")
    except Exception as e:
        print(f"[WARN] Error parsing release response: {e}")
    return None


def upload_asset(upload_url: str, file_path: Path) -> str | None:
    """Sube un archivo al release y retorna la URL de descarga."""
    if not file_path.exists():
        print(f"[SKIP] Archivo no encontrado: {file_path}")
        return None

    filename = file_path.name
    url = f"{upload_url}?name={filename}"
    size_mb = file_path.stat().st_size / 1024 / 1024
    print(f"  [UPLOAD] {filename} ({size_mb:.1f} MB)...")

    result = subprocess.run([
        "curl", "-s", "-X", "POST", url,
        "-H", f"Authorization: Bearer {GITHUB_TOKEN}",
        "-H", "Content-Type: video/mp4",
        "--data-binary", f"@{file_path}"
    ], capture_output=True, text=True, timeout=300)

    try:
        data = json.loads(result.stdout)
        browser_url = data.get("browser_download_url", "")
        if browser_url:
            print(f"  [OK] URL: {browser_url}")
            return browser_url
        print(f"  [WARN] Upload response: {result.stdout[:200]}")
    except Exception as e:
        print(f"  [WARN] Error parsing upload: {e}")
    return None


def main():
    print(f"\n{'='*60}")
    print(f"GITHUB RELEASE UPLOADER — Sprint {SPRINT_N}")
    print(f"{'='*60}")

    pub_dir = VAULT / "40_Publicacion"
    sched_files = sorted(pub_dir.glob(f"schedule_sprint{SPRINT_N}.json"), reverse=True)
    if not sched_files:
        print("[SKIP] Sin schedule.json.")
        return

    sched_path = sched_files[0]
    schedule = json.loads(sched_path.read_text(encoding="utf-8"))

    # Encontrar videos que tienen path local pero no URL pública
    pending = [v for v in schedule.get("videos", [])
               if v.get("local_video_path") and not v.get("video_url")]

    if not pending:
        print("[INFO] Todos los videos ya tienen URL o no tienen path local.")
        return

    upload_url = create_github_release()
    if not upload_url:
        print("[FAIL] No se pudo crear el release.")
        return

    updated = 0
    for video in pending:
        local_path = Path(video["local_video_path"])
        url = upload_asset(upload_url, local_path)
        if url:
            video["video_url"] = url
            updated += 1

    sched_path.write_text(
        json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n[DONE] {updated} URLs asignadas en schedule.")


if __name__ == "__main__":
    main()
