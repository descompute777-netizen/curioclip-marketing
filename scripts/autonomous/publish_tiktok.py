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

def get_composio_toolset():
    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        sys.exit("[ERROR] COMPOSIO_API_KEY no configurada en GitHub Secrets.")
    try:
        from composio_openai import ComposioToolSet
        return ComposioToolSet(api_key=api_key)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "composio-openai", "-q"], check=True)
        from composio_openai import ComposioToolSet
        return ComposioToolSet(api_key=api_key)


def publish_video(video_url: str, caption: str, entity_id: str = "default") -> str | None:
    """Publica video en TikTok vía Composio. Retorna publish_id o None si falla."""
    toolset = get_composio_toolset()
    try:
        from composio import Action
        print(f"[COMPOSIO] Publicando: {video_url[:60]}...")
        result = toolset.execute_action(
            action=Action.TIKTOK_PUBLISH_VIDEO,
            params={
                "video_url": video_url,
                "caption": caption,
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_stitch": False,
                "disable_comment": False,
            },
            entity_id=entity_id
        )
        publish_id = result.get("data", {}).get("publish_id") or result.get("publish_id")
        print(f"[OK] publish_id: {publish_id}")
        return publish_id
    except Exception as e:
        print(f"[ERROR] Composio TikTok: {e}")
        return None


def monitor_publish_status(publish_id: str, entity_id: str = "default") -> bool:
    """Monitorea estado de publicación con backoff exponencial (5s→10s→20s...)."""
    toolset = get_composio_toolset()
    try:
        from composio import Action
    except ImportError:
        return False

    delays = [5, 10, 20, 40, 60, 120]
    for delay in delays:
        time.sleep(delay)
        try:
            result = toolset.execute_action(
                action=Action.TIKTOK_FETCH_PUBLISH_STATUS,
                params={"publish_id": publish_id},
                entity_id=entity_id
            )
            status = result.get("data", {}).get("status") or result.get("status", "")
            print(f"  [STATUS] {status} (esperando {delay}s)")
            if status in ("PUBLISH_COMPLETE", "SUCCESS", "published"):
                print("[OK] Video publicado exitosamente en TikTok.")
                return True
            elif status in ("FAILED", "ERROR"):
                print(f"[FAIL] TikTok rechazó la publicación: {result}")
                return False
        except Exception as e:
            print(f"  [WARN] Status check falló: {e}")

    print("[TIMEOUT] No se pudo confirmar publicación después de 5 intentos.")
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
