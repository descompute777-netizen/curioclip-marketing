"""
Auto-Editor V5: Plomo Fundido
==============================
Compone automaticamente el video V5 a partir de:
  - V5_PlomoFundido.mp3 (voiceover existente)
  - V5_PlomoFundido.srt (subtitulos generados con Whisper)
  - B-roll descargado de Pexels (CC0)
  - Overlays de texto via ffmpeg drawtext

Salida:
  - obsidian_vault/SEMANAS/SEMANA_01_2026-05-06_a_2026-05-12/VIERNES/OUTPUT/V5_final.mp4
  - obsidian_vault/SEMANAS/.../VIERNES/OUTPUT/V5_thumbnail.png
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import json
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

import static_ffmpeg
static_ffmpeg.add_paths()

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_01_2026-05-06_a_2026-05-12" / "VIERNES"
OUT = SEMANA / "OUTPUT"
SOURCE = SEMANA / "SOURCE"
VOICEOVER = ROOT / "obsidian_vault" / "30_Contenido" / "audios_generados" / "V5_PlomoFundido.mp3"
SRT = ROOT / "obsidian_vault" / "30_Contenido" / "audios_generados" / "V5_PlomoFundido.srt"

OUT.mkdir(parents=True, exist_ok=True)
SOURCE.mkdir(parents=True, exist_ok=True)


def download_pexels_video(video_id: str, dest: Path) -> Path:
    """Descarga un video de Pexels via su URL directa /download/video/<id>/."""
    url = f"https://www.pexels.com/download/video/{video_id}/"
    print(f"[DL] {url} -> {dest.name}")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            with open(dest, "wb") as f:
                while chunk := r.read(65536):
                    f.write(chunk)
        print(f"[OK] {dest.stat().st_size//1024} KB")
        return dest
    except urllib.error.HTTPError as e:
        print(f"[FAIL] HTTP {e.code}")
        return None


# Lista curada de Pexels video IDs por segmento (basado en brief V5)
# Estos IDs son los TOP results para cada query relevante
BROLL_PLAN = [
    {"seg": "0-3", "query": "molten metal", "id": "5121751", "duration": 3.0,
     "desc": "Plomo brillando — hook visual"},
    {"seg": "3-9", "query": "metal foundry", "id": "33939016", "duration": 6.0,
     "desc": "Plomo fundido siendo vertido"},
    {"seg": "9-15", "query": "water hot pan", "id": "5121754", "duration": 6.0,
     "desc": "Demostracion del efecto"},
    {"seg": "15-22", "query": "molten steel slow motion", "id": "5121751", "duration": 7.0,
     "desc": "Slow motion de cierre"},
    {"seg": "22-35", "query": "science laboratory", "id": "33939016", "duration": 12.0,
     "desc": "Cierre + CTA"},
]


def srt_to_ass(srt_path: Path, ass_path: Path, video_w: int = 1080, video_h: int = 1920):
    """Convierte SRT a ASS con PlayRes correcto + estilo TikTok-friendly.

    Bug previo: SRT se convertia internamente con PlayResY=288 -> texto se veia 6.67x mas grande.
    Fix: ASS explicito con PlayRes = video real y valores en pixels reales.

    Estilo TikTok:
      - Bottom center, ~150px del fondo (encima de UI buttons de TikTok)
      - Bold blanco con outline negro grueso (3px) — legible sobre cualquier fondo
      - Fontsize 52px — tamano optimo para mobile reading
      - Max line: ~30 chars (auto-wrap por ffmpeg)
    """
    import re

    fontsize = 52
    outline = 3
    shadow = 1
    margin_v = 220   # px desde el bottom — alto para que no choque con UI nativa de TikTok
    margin_lr = 80   # padding lateral

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_w}
PlayResY: {video_h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{fontsize},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},2,{margin_lr},{margin_lr},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    srt_text = srt_path.read_text(encoding="utf-8")
    # Parse blocks: index\n start --> end \n text(s) \n\n
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    events = []
    for blk in blocks:
        lines = blk.strip().splitlines()
        if len(lines) < 3:
            continue
        ts = lines[1]
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", ts)
        if not m:
            continue
        sh, sm, ss, sms, eh, em, es, ems = m.groups()
        # ASS time: H:MM:SS.cc (centiseconds, 2 digits)
        s_ass = f"{int(sh)}:{int(sm):02d}:{int(ss):02d}.{int(sms[:2]):02d}"
        e_ass = f"{int(eh)}:{int(em):02d}:{int(es):02d}.{int(ems[:2]):02d}"
        text = " ".join(lines[2:]).strip()
        text = text.replace("\n", "\\N")
        # Forzar 2 lineas max — split en mitad si es muy largo
        if len(text) > 32:
            words = text.split()
            mid = len(words) // 2
            text = " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])
        events.append(f"Dialogue: 0,{s_ass},{e_ass},Default,,0,0,0,,{text}")

    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    print(f"[ASS] {len(events)} dialogos -> {ass_path}")


def step_1_download_broll():
    print("\n=== PASO 1: DESCARGAR B-ROLL ===")
    downloaded = []
    seen = set()
    for plan in BROLL_PLAN:
        if plan["id"] in seen:
            # Reusar
            existing = SOURCE / f"broll_{plan['id']}.mp4"
            if existing.exists():
                print(f"[REUSE] broll_{plan['id']}.mp4 para segmento {plan['seg']}")
                downloaded.append({**plan, "path": existing})
                continue
        dest = SOURCE / f"broll_{plan['id']}.mp4"
        if dest.exists() and dest.stat().st_size > 100000:
            print(f"[SKIP] {dest.name} ya existe ({dest.stat().st_size//1024} KB)")
            downloaded.append({**plan, "path": dest})
            seen.add(plan["id"])
            continue
        result = download_pexels_video(plan["id"], dest)
        if result:
            downloaded.append({**plan, "path": result})
            seen.add(plan["id"])
    return downloaded


def step_2_compose_video(broll_list, voiceover, srt_path, output):
    """Compone el video final con ffmpeg."""
    print("\n=== PASO 2: COMPOSICION FFMPEG ===")

    # 9:16 1080x1920 target
    W, H = 1080, 1920

    # Construir cadena de B-roll: trim cada uno a su duracion + scale a 1080x1920
    inputs = []
    filter_parts = []
    concat_inputs = []

    for i, clip in enumerate(broll_list):
        inputs.extend(["-i", str(clip["path"])])
        # trim + scale + crop a 9:16
        filter_parts.append(
            f"[{i}:v]trim=duration={clip['duration']},setpts=PTS-STARTPTS,"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H}[v{i}]"
        )
        concat_inputs.append(f"[v{i}]")

    # Agregar voiceover como input final
    inputs.extend(["-i", str(voiceover)])
    voiceover_idx = len(broll_list)

    # Concat de todos los B-roll
    filter_parts.append(
        "".join(concat_inputs) + f"concat=n={len(broll_list)}:v=1:a=0[vbase]"
    )

    # Subtitulos: convertir SRT -> ASS con PlayRes 1080x1920 + styling proporcional
    local_ass = Path("./subs_v5.ass")
    srt_to_ass(srt_path, local_ass, video_w=W, video_h=H)
    sub_filter = "[vbase]subtitles=subs_v5.ass[vsubs]"
    filter_parts.append(sub_filter)

    # Cada drawtext en su propia chain con escape de comas en between()
    # Hook 0-3s — mas chico (42px) y con line break manual para que no se corte
    filter_parts.append(
        "[vsubs]drawtext=text='METIO SU MANO EN':"
        "fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=68:"
        "fontcolor=white:bordercolor=black:borderw=4:"
        "x=(w-text_w)/2:y=180:enable='between(t\\,0\\,3)'[vh1];"
        "[vh1]drawtext=text='PLOMO FUNDIDO':"
        "fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=92:"
        "fontcolor=yellow:bordercolor=black:borderw=5:"
        "x=(w-text_w)/2:y=270:enable='between(t\\,0\\,3)'[vhook]"
    )
    # Warning line 1 (14-19s)
    filter_parts.append(
        "[vhook]drawtext=text='SOLO FUNCIONA MILISEGUNDOS':"
        "fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=52:"
        "fontcolor=red:bordercolor=white:borderw=3:"
        "x=(w-text_w)/2:y=h/2-100:enable='between(t\\,14\\,19)'[vw1]"
    )
    # Warning line 2 (14-19s)
    filter_parts.append(
        "[vw1]drawtext=text='NO INTENTAR EN CASA':"
        "fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=48:"
        "fontcolor=red:bordercolor=white:borderw=3:"
        "x=(w-text_w)/2:y=h/2:enable='between(t\\,14\\,19)'[vw2]"
    )
    # CTA line 1 (28-35s)
    filter_parts.append(
        "[vw2]drawtext=text='SIGUEME PARA MAS':"
        "fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=64:"
        "fontcolor=yellow:bordercolor=black:borderw=4:"
        "x=(w-text_w)/2:y=h/2:enable='between(t\\,28\\,35)'[vc1]"
    )
    # CTA line 2 (28-35s)
    filter_parts.append(
        "[vc1]drawtext=text='@curioclip':"
        "fontfile='C\\:/Windows/Fonts/arialbd.ttf':fontsize=42:"
        "fontcolor=white:bordercolor=black:borderw=3:"
        "x=(w-text_w)/2:y=h/2+90:enable='between(t\\,28\\,35)'[vfinal]"
    )

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vfinal]",
        "-map", f"{voiceover_idx}:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        str(output),
    ]
    print(f"[FFMPEG] Componiendo {output.name}...")
    print(f"[CMD] {' '.join(str(c) for c in cmd[:8])}...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] ffmpeg exit {r.returncode}")
        print(r.stderr[-2000:])
        return None
    print(f"[OK] {output.name} -> {output.stat().st_size//1024} KB")
    return output


def step_3_thumbnail(video_path, output):
    """Extrae frame 0 + agrega texto del hook."""
    print("\n=== PASO 3: THUMBNAIL ===")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-ss", "0.5", "-vframes", "1",
        "-vf",
        "drawtext=text='METIO SU MANO EN':fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        "fontsize=78:fontcolor=white:bordercolor=black:borderw=5:"
        "x=(w-text_w)/2:y=300,"
        "drawtext=text='PLOMO FUNDIDO':fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        "fontsize=98:fontcolor=yellow:bordercolor=black:borderw=5:"
        "x=(w-text_w)/2:y=400,"
        "drawtext=text='327 GRADOS':fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        "fontsize=88:fontcolor=red:bordercolor=white:borderw=4:"
        "x=(w-text_w)/2:y=520",
        str(output),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] {r.stderr[-1000:]}")
        return None
    print(f"[OK] {output.name}")
    return output


def main():
    if not VOICEOVER.exists():
        print(f"[FAIL] Voiceover no encontrado: {VOICEOVER}")
        return
    if not SRT.exists():
        print(f"[WARN] SRT no encontrado todavia: {SRT}")
        print("       Ejecuta primero: python src/pipeline/transcribe_v5.py")
        return

    broll = step_1_download_broll()
    if not broll:
        print("[FAIL] No se descargo ningun B-roll")
        return

    final = OUT / "V5_final.mp4"
    result = step_2_compose_video(broll, VOICEOVER, SRT, final)
    if not result:
        return

    thumb = OUT / "V5_thumbnail.png"
    step_3_thumbnail(result, thumb)

    print("\n" + "=" * 60)
    print("AUTO-EDITOR V5: COMPLETADO")
    print("=" * 60)
    print(f"Video final: {final}")
    print(f"Thumbnail:   {thumb}")
    print()
    print("Para revisar: abre el archivo MP4. Para iterar: ajusta BROLL_PLAN.")


if __name__ == "__main__":
    main()
