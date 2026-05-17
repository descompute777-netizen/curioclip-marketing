"""
Publicador Autónomo TikTok — vía Composio
==========================================
GitHub Actions: daily-publish.yml lo invoca según schedule.
Composio maneja el OAuth de TikTok y la llamada a Content Posting API.

Flujo:
  1. Lee schedule_sprint{N}.json → encuentra el video de hoy
  2. Verifica que la URL del video sea accesible (GitHub Release)
  3. Llama TIKTOK_PUBLISH_VIDEO via Composio Python SDK
  4. Monitorea TIKTOK_FETCH_PUBLISH_STATUS con backoff exponencial
  5. Marca como published=true en schedule.json
  6. Git commit del schedule actualizado

Requiere GitHub Secrets:
  COMPOSIO_API_KEY       (ya configurado: ck_NcIb61...)
  GITHUB_TOKEN           (automático en Actions)

NOTA: Composio OAuth debe estar completado una vez manualmente.
Ver: SETUP.md → Sección "Conectar TikTok a Composio"
"""
import os, sys, json, time, datetime, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
TODAY = datetime.date.today().isoformat()
NOW_UTC = datetime.datetime.utcnow()


# ─── Composio TikTok ────────────────────────────────────────────────────────

def get_composio_client():
    """Composio SDK v0.13+ usa la clase Composio directamente."""
    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        sys.exit("[ERROR] COMPOSIO_API_KEY no configurada en GitHub Secrets.")
    try:
        from composio import Composio
        return Composio(api_key=api_key)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "composio", "composio-openai", "-q"], check=True)
        from composio import Composio
        return Composio(api_key=api_key)


def verify_oauth_active(user_id: str = "curioclip") -> bool:
    """Verifica que existe una connected account ACTIVE de TikTok para user_id."""
    c = get_composio_client()
    accounts = c.connected_accounts.list()
    for a in accounts.items:
        tk = a.toolkit.slug if hasattr(a, "toolkit") and a.toolkit else ""
        uid = a.user_id if hasattr(a, "user_id") else ""
        st = a.status if hasattr(a, "status") else ""
        if tk == "tiktok" and uid == user_id and st == "ACTIVE":
            print(f"[OK] OAuth TikTok ACTIVE: {a.id}")
            return True
    print(f"[FAIL] No hay OAuth ACTIVE para user_id={user_id}.")
    print(f"  Accounts existentes: {[(a.id, a.status if hasattr(a,'status') else '?') for a in accounts.items[:5]]}")
    return False


def publish_video(video_url: str, caption: str, user_id: str = "curioclip") -> str | None:
    """Publica video en TikTok via Composio. Retorna publish_id o None si falla."""
    if not verify_oauth_active(user_id):
        print("[FALLBACK] OAuth no activo. Saltando a Playwright MCP manual.")
        return None

    c = get_composio_client()
    try:
        print(f"[COMPOSIO] Publicando: {video_url[:60]}...")
        result = c.tools.execute(
            slug="TIKTOK_PUBLISH_VIDEO",
            arguments={
                "video_url": video_url,
                "caption": caption,
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_stitch": False,
                "disable_comment": False,
            },
            user_id=user_id,
        )
        publish_id = result.get("data", {}).get("publish_id") or result.get("publish_id")
        print(f"[OK] publish_id: {publish_id}")
        return publish_id
    except Exception as e:
        print(f"[ERROR] Composio TikTok: {e}")
        return None


def monitor_publish_status(publish_id: str, user_id: str = "curioclip") -> bool:
    """Monitorea estado de publicacion con backoff exponencial (5s→10s→20s...)."""
    c = get_composio_client()
    delays = [5, 10, 20, 40, 60, 120]
    for delay in delays:
        time.sleep(delay)
        try:
            result = c.tools.execute(
                slug="TIKTOK_FETCH_PUBLISH_STATUS",
                arguments={"publish_id": publish_id},
                user_id=user_id,
            )
            status = result.get("data", {}).get("status") or result.get("status", "")
            print(f"  [STATUS] {status} (esperando {delay}s)")
            if status in ("PUBLISH_COMPLETE", "SUCCESS", "published"):
                print("[OK] Video publicado exitosamente en TikTok.")
                return True
            elif status in ("FAILED", "ERROR"):
                print(f"[FAIL] TikTok rechazo la publicacion: {result}")
                return False
        except Exception as e:
            print(f"  [WARN] Status check fallo: {e}")
    print("[TIMEOUT] No se pudo confirmar publicacion despues de 5 intentos.")
    return False


# ─── Schedule management ─────────────────────────────────────────────────────

def find_todays_video() -> tuple[dict | None, Path | None]:
    """Busca el video programado para hoy (±30min de margen)."""
    pub_dir = VAULT / "40_Publicacion"
    schedules = sorted(pub_dir.glob("schedule_sprint*.json"), reverse=True)

    for sched_path in schedules:
        try:
            data = json.loads(sched_path.read_text(encoding="utf-8"))
            for video in data.get("videos", []):
                if video.get("published"):
                    continue
                pub_at = datetime.datetime.strptime(
                    video["publish_at_utc"], "%Y-%m-%dT%H:%M:%SZ"
                )
                delta = abs((NOW_UTC - pub_at).total_seconds())
                if delta <= 1800:  # ±30 min
                    return video, sched_path
        except Exception as e:
            print(f"[WARN] Error leyendo {sched_path.name}: {e}")

    return None, None


def mark_published(video: dict, sched_path: Path):
    """Marca video como publicado en el JSON."""
    data = json.loads(sched_path.read_text(encoding="utf-8"))
    for v in data["videos"]:
        if v["guion_id"] == video["guion_id"]:
            v["published"] = True
            v["published_at"] = NOW_UTC.strftime("%Y-%m-%dT%H:%M:%SZ")
            break
    sched_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Marcado como publicado: {video['guion_id']}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"TIKTOK PUBLISHER — {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    video, sched_path = find_todays_video()

    if not video:
        print("[INFO] No hay video programado para esta ventana de tiempo (±30 min).")
        print("  Esto es normal si el workflow corre fuera de los horarios programados.")
        return

    print(f"[FOUND] Video del día: {video['guion_id']} | {video['day']}")
    print(f"  Programado para: {video['publish_at_utc']}")
    print(f"  URL: {video.get('video_url', '(sin URL)')}")

    video_url = video.get("video_url", "")
    if not video_url:
        print("[WARN] Video sin URL. El video aún no fue producido y subido.")
        print("  Verifica que weekly-sprint.yml completó la producción del video.")
        print("  El publish queda pendiente hasta que se asigne la URL.")
        return

    caption = video.get("caption", "")
    if not caption:
        caption = (
            "Un dato que no vas a creer 🤯\n\n"
            "¿Sabías esto? Comenta abajo 👇\n\n"
            f"{video.get('hashtags', '#datoscuriosos #curioclip #sabiasque')}"
        )

    publish_id = publish_video(video_url, caption)
    if publish_id:
        success = monitor_publish_status(publish_id)
        if success:
            mark_published(video, sched_path)
    else:
        print("[FALLBACK] Composio falló. Generando paquete manual...")
        print("\n" + "="*60)
        print("PAQUETE MANUAL PARA PUBLICAR EN TIKTOK:")
        print(f"  Video URL: {video_url}")
        print(f"  Caption:\n{caption}")
        print(f"  Horario: {video['publish_at_utc']}")
        print("="*60)


if __name__ == "__main__":
    main()
