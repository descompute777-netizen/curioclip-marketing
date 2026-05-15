"""
Productor de Video en la Nube — GitHub Actions
================================================
Genera videos completos sin intervención humana:
  1. Lee schedule.json → encuentra guiones pendientes de esta semana
  2. Genera voiceover con edge-tts (GRATIS)
  3. Descarga B-roll de Pexels CC0 (API gratis)
  4. Compone video 9:16 1080x1920 con ffmpeg
  5. Guarda en SEMANA_XX/DIA/OUTPUT/

Después de este script, upload_release.py sube a GitHub Releases.
"""
import os, sys, json, subprocess, datetime, re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
SEMANAS_DIR = VAULT / "SEMANAS"
TODAY = datetime.date.today().isoformat()
SPRINT_N = ((datetime.date.today() - datetime.date(2026, 5, 6)).days // 7) + 1
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# Pexels queries por sub-nicho (términos que dan B-roll CC0 de calidad)
BROLL_QUERIES = {
    "misterio":    ["abandoned building", "mystery dark", "forest night"],
    "ciencia":     ["science laboratory", "physics experiment", "particles"],
    "historia":    ["old map", "ancient civilization", "history document"],
    "psicologia":  ["human brain", "neural network", "mind psychology"],
    "cosmologia":  ["galaxy space", "stars universe", "milky way"],
    "default":     ["science", "dark background", "technology"],
}


def detect_subniche(guion_text: str) -> str:
    text_lower = guion_text.lower()
    if any(w in text_lower for w in ["misterio", "señal", "desapareci", "inexplicable"]):
        return "misterio"
    if any(w in text_lower for w in ["fisica", "química", "bacteria", "temperatura"]):
        return "ciencia"
    if any(w in text_lower for w in ["napoleon", "guerra", "historia", "medieval"]):
        return "historia"
    if any(w in text_lower for w in ["cerebro", "deja vu", "psicolog", "cosquillas"]):
        return "psicologia"
    if any(w in text_lower for w in ["galaxia", "sol", "universo", "luna", "espacio"]):
        return "cosmologia"
    return "default"


def search_pexels_video(query: str) -> str | None:
    """Busca video CC0 en Pexels y retorna URL de descarga."""
    if not PEXELS_API_KEY:
        return None
    import urllib.request, json as _json
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=5&orientation=portrait"
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = _json.loads(r.read())
            videos = data.get("videos", [])
            if not videos:
                return None
            # Buscar el video de mayor resolución disponible ≤ 1080p
            for vid in videos:
                for vf in vid.get("video_files", []):
                    if vf.get("width", 0) >= 720 and vf.get("height", 0) >= 1280:
                        return vf["link"]
                # Fallback: cualquier archivo
                if vid.get("video_files"):
                    return vid["video_files"][0]["link"]
    except Exception as e:
        print(f"  [WARN] Pexels search falló: {e}")
    return None


def download_video(url: str, dest: Path) -> bool:
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            with open(dest, "wb") as f:
                while chunk := r.read(65536):
                    f.write(chunk)
        return dest.stat().st_size > 10000
    except Exception as e:
        print(f"  [WARN] Download falló: {e}")
        return False


def generate_voiceover_async(text: str, output: Path) -> bool:
    """Genera voiceover con edge-tts."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "edge_tts",
             "--voice", "es-MX-JorgeNeural",
             "--rate", "+10%",
             "--text", text[:3000],
             "--write-media", str(output)],
            capture_output=True, timeout=60
        )
        return result.returncode == 0 and output.exists() and output.stat().st_size > 1000
    except Exception as e:
        print(f"  [WARN] edge-tts falló: {e}")
        return False


def compose_video(broll_paths: list[Path], voiceover: Path, output: Path,
                  hook_text: str = "", cta_text: str = "") -> bool:
    """Compone video 9:16 con ffmpeg."""
    W, H = 1080, 1920
    FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

    inputs = []
    filter_parts = []
    concat_parts = []

    # Duración total basada en el voiceover
    # Obtenemos duración del voiceover
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(voiceover)],
            capture_output=True, text=True, timeout=10
        )
        total_duration = float(result.stdout.strip() or "30")
    except Exception:
        total_duration = 30.0

    # Distribuir duración entre clips
    n_clips = len(broll_paths)
    if n_clips == 0:
        print("[FAIL] Sin B-roll disponible")
        return False

    clip_duration = total_duration / n_clips

    for i, clip in enumerate(broll_paths):
        inputs.extend(["-i", str(clip)])
        filter_parts.append(
            f"[{i}:v]trim=duration={clip_duration:.1f},setpts=PTS-STARTPTS,"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H}[v{i}]"
        )
        concat_parts.append(f"[v{i}]")

    inputs.extend(["-i", str(voiceover)])
    vo_idx = n_clips

    filter_parts.append(f"{''.join(concat_parts)}concat=n={n_clips}:v=1:a=0[vbase]")

    # Hook text (0-3s)
    current = "vbase"
    if hook_text:
        safe_hook = hook_text[:50].replace("'", "\\'").replace(":", "\\:")
        filter_parts.append(
            f"[{current}]drawtext=text='{safe_hook}':"
            f"fontfile='{FONT}':fontsize=72:"
            f"fontcolor=white:bordercolor=black:borderw=5:"
            f"x=(w-text_w)/2:y=200:enable='between(t\\,0\\,3)'[vtxt1]"
        )
        current = "vtxt1"

    # CTA text (últimos 5s)
    if cta_text:
        safe_cta = cta_text[:40].replace("'", "\\'").replace(":", "\\:")
        filter_parts.append(
            f"[{current}]drawtext=text='{safe_cta}':"
            f"fontfile='{FONT}':fontsize=56:"
            f"fontcolor=yellow:bordercolor=black:borderw=4:"
            f"x=(w-text_w)/2:y=h-300:"
            f"enable='between(t\\,{total_duration-5:.0f}\\,{total_duration:.0f})'[vfinal]"
        )
        current = "vfinal"

    if current == "vbase":
        filter_parts.append(f"[vbase]null[vfinal]")

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vfinal]",
        "-map", f"{vo_idx}:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        str(output)
    ]

    print(f"  [FFMPEG] Componiendo {output.name}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"  [FAIL] ffmpeg: {result.stderr[-500:]}")
        return False
    size_mb = output.stat().st_size / 1024 / 1024
    print(f"  [OK] {output.name} → {size_mb:.1f} MB")
    return True


def produce_video_from_schedule(video_entry: dict, out_dir: Path, tmp_dir: Path) -> Path | None:
    """Produce un video completo a partir de una entrada del schedule."""
    guion_id = video_entry["guion_id"]
    caption = video_entry.get("caption", "")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Extraer hook y CTA del caption
    lines = caption.split("\n") if caption else []
    hook_text = lines[0][:50] if lines else ""
    cta_text = lines[-2][:40] if len(lines) >= 2 else "Sígueme para más"

    # Detectar sub-nicho del caption
    subniche = detect_subniche(caption)
    queries = BROLL_QUERIES.get(subniche, BROLL_QUERIES["default"])
    print(f"\n[PRODUCE] {guion_id} | sub-nicho: {subniche}")

    # 1. Generar voiceover
    vo_text = caption if caption else f"Un dato increíble que no vas a creer. {guion_id}."
    vo_path = tmp_dir / f"{guion_id}_voice.mp3"
    print(f"  [TTS] Generando voiceover...")
    vo_ok = generate_voiceover_async(vo_text, vo_path)
    if not vo_ok:
        print(f"  [WARN] Voiceover falló para {guion_id}")
        return None

    # 2. Descargar B-roll
    broll_paths = []
    for query in queries[:3]:  # máx 3 clips
        url = search_pexels_video(query)
        if url:
            dest = tmp_dir / f"broll_{len(broll_paths)}.mp4"
            print(f"  [DL] B-roll: {query}")
            if download_video(url, dest):
                broll_paths.append(dest)

    if not broll_paths:
        print(f"  [WARN] Sin B-roll para {guion_id} — usando color sólido")
        # Generar video de color sólido como fallback
        solid = tmp_dir / "solid_bg.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "color=c=black:s=1080x1920:r=30",
            "-t", "35", "-c:v", "libx264", str(solid)
        ], capture_output=True, timeout=30)
        if solid.exists():
            broll_paths = [solid]
        else:
            return None

    # 3. Componer video
    out_path = out_dir / f"{guion_id}_final.mp4"
    success = compose_video(broll_paths, vo_path, out_path, hook_text, cta_text)
    return out_path if success else None


def main():
    print(f"\n{'='*60}")
    print(f"CLOUD PRODUCER — Sprint {SPRINT_N} — {TODAY}")
    print(f"{'='*60}")

    # Leer schedule
    pub_dir = VAULT / "40_Publicacion"
    sched_files = sorted(pub_dir.glob(f"schedule_sprint{SPRINT_N}.json"), reverse=True)
    if not sched_files:
        print(f"[INFO] No hay schedule para sprint {SPRINT_N}. Buscando cualquier schedule...")
        sched_files = sorted(pub_dir.glob("schedule_sprint*.json"), reverse=True)

    if not sched_files:
        print("[SKIP] Sin schedule.json. El weekly_sprint.py debe correr primero.")
        return

    sched_path = sched_files[0]
    schedule = json.loads(sched_path.read_text(encoding="utf-8"))
    sprint = schedule.get("sprint", SPRINT_N)
    week_start = schedule.get("week_start", TODAY)

    print(f"[SCHED] Sprint {sprint} | Semana: {week_start}")

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        produced = 0

        for video in schedule.get("videos", []):
            if video.get("video_url"):
                print(f"  [SKIP] {video['guion_id']} ya tiene URL, omitiendo.")
                continue

            day = video.get("day", "lunes").upper()
            semana_dir = SEMANAS_DIR / f"SEMANA_{sprint:02d}_{week_start}_auto"
            out_dir = semana_dir / day / "OUTPUT"

            result = produce_video_from_schedule(video, out_dir, tmp_dir)
            if result:
                # Guardar path relativo para upload_release.py
                video["local_video_path"] = str(result)
                produced += 1
                print(f"  [OK] {video['guion_id']} → {result}")

        # Actualizar schedule con paths locales
        sched_path.write_text(
            json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(f"\n[DONE] {produced} videos producidos.")


if __name__ == "__main__":
    main()
