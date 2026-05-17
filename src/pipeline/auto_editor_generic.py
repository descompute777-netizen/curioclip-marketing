"""
Auto-Editor Genérico — CurioClip
=================================
Generalización de auto_editor_v5.py que produce cualquier video del pipeline
a partir de una configuración por diccionario.

Uso:
    from src.pipeline.auto_editor_generic import produce_video
    from configs.v2_bacterias import VIDEO_CONFIG
    produce_video(VIDEO_CONFIG)

O desde CLI:
    python -m src.pipeline.auto_editor_generic --config configs/v2_bacterias.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import re
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

import static_ffmpeg
static_ffmpeg.add_paths()

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
AUDIO_DIR = ROOT / "obsidian_vault" / "30_Contenido" / "audios_generados"
FONTS_DIR = Path(r"C:\Windows\Fonts")
FONT_BOLD = str(FONTS_DIR / "arialbd.ttf").replace("\\", "/").replace("C:", "C\\:")
W, H = 1080, 1920


def download_pexels_video(video_id: str, dest: Path) -> Path | None:
    url = f"https://www.pexels.com/download/video/{video_id}/"
    print(f"  [DL] {url} -> {dest.name}")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            with open(dest, "wb") as f:
                while chunk := r.read(65536):
                    f.write(chunk)
        size_kb = dest.stat().st_size // 1024
        print(f"  [OK] {size_kb} KB")
        return dest
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] HTTP {e.code} para video_id={video_id}")
        return None


def srt_to_ass(srt_path: Path, ass_path: Path, fontsize: int = 58):
    """Convierte SRT → ASS optimizado para SAFE ZONE de TikTok.

    Safe zone TikTok (1080x1920):
      - Top UI (header/sound): 0–250px
      - Bottom UI (avatar/desc/comments): 1480–1920px (~440px)
      - Right UI (interaction buttons): x>950
      - Safe area central: ~250–1480 vertical, 60–950 horizontal
    Subtitulos: Alignment=2 (bottom-center) + MarginV=420 → quedan ENCIMA
    de la UI bottom de TikTok, ~Y=1500 en el video 1920 alto.
    """
    margin_v = 420   # px desde el FONDO — encima del UI overlay de TikTok
    margin_lr = 80   # margen lateral, evita right UI (botones)
    outline = 5      # borde mas grueso para legibilidad maxima
    shadow = 3

    # BorderStyle 3 = caja opaca (background box detras del texto) — maxima legibilidad
    # BackColour 0xB0000000 = negro con 70% opacidad
    header = (
        f"[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {W}\nPlayResY: {H}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        f"[V4+ Styles]\n"
        f"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        f"BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        f"BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,Arial,{fontsize},&H00FFFFFF,&H00FFFFFF,&H00000000,&HB0000000,"
        f"-1,0,0,0,100,100,1,0,1,{outline},{shadow},2,{margin_lr},{margin_lr},{margin_v},1\n\n"
        f"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    srt_text = srt_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    events = []
    for blk in blocks:
        lines = blk.strip().splitlines()
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1])
        if not m:
            continue
        sh, sm, ss, sms, eh, em, es, ems = m.groups()
        s_ass = f"{int(sh)}:{int(sm):02d}:{int(ss):02d}.{int(sms[:2]):02d}"
        e_ass = f"{int(eh)}:{int(em):02d}:{int(es):02d}.{int(ems[:2]):02d}"
        text = " ".join(lines[2:]).strip().replace("\n", "\\N")
        if len(text) > 32:
            words = text.split()
            mid = len(words) // 2
            text = " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])
        events.append(f"Dialogue: 0,{s_ass},{e_ass},Default,,0,0,0,,{text}")

    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    print(f"  [ASS] {len(events)} diálogos → {ass_path.name}")


def produce_video(cfg: dict) -> Path | None:
    """
    Produce un video completo a partir de un config dict.

    Config keys (requeridos):
        video_id    str             — identificador del video (ej: "V2")
        voiceover   str|Path        — nombre del .mp3 en audios_generados/
        broll_plan  list[dict]      — cada item: {seg, id, duration, desc}
        overlays    list[dict]      — drawtext filters: {text, fontsize, color, y, t_start, t_end}
        output_dir  str|Path        — carpeta de salida (se crea si no existe)

    Config keys (opcionales):
        srt_file    str|Path        — nombre del .srt (default: mismo nombre que voiceover)
        subtitle_fontsize int       — fontsize de subtítulos (default: 52)
        thumbnail_texts list[dict]  — textos para el thumbnail (default: primer overlay)
        duration_s  float           — duración máxima en segundos (default: longest broll)
    """
    video_id = cfg["video_id"]
    voiceover_path = AUDIO_DIR / cfg["voiceover"]
    srt_name = cfg.get("srt_file", cfg["voiceover"].replace(".mp3", ".srt"))
    srt_path = AUDIO_DIR / srt_name
    output_dir = Path(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    source_dir = output_dir.parent / "SOURCE"
    source_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"AUTO-EDITOR: {video_id}")
    print(f"{'='*60}")

    if not voiceover_path.exists():
        print(f"[FAIL] Voiceover no encontrado: {voiceover_path}")
        return None
    if not srt_path.exists():
        print(f"[WARN] SRT no encontrado: {srt_path} — subtítulos omitidos")

    # PASO 1: Descargar B-roll
    print("\n--- PASO 1: DESCARGAR B-ROLL ---")
    broll_list = []
    seen_ids = {}
    for plan in cfg["broll_plan"]:
        vid_id = plan["id"]
        dest = source_dir / f"broll_{vid_id}.mp4"
        if dest.exists() and dest.stat().st_size > 100_000:
            print(f"  [SKIP] {dest.name} ya existe")
        elif vid_id in seen_ids:
            dest = seen_ids[vid_id]
        else:
            result = download_pexels_video(vid_id, dest)
            if not result:
                print(f"  [WARN] Omitiendo segmento {plan.get('seg','?')} — descarga fallida")
                continue
        seen_ids[vid_id] = dest
        broll_list.append({**plan, "path": dest})

    if not broll_list:
        print("[FAIL] No se descargó ningún B-roll")
        return None

    # PASO 2: Composición ffmpeg
    print("\n--- PASO 2: COMPOSICIÓN FFMPEG ---")
    inputs = []
    filter_parts = []
    concat_inputs = []

    for i, clip in enumerate(broll_list):
        inputs.extend(["-i", str(clip["path"])])
        filter_parts.append(
            f"[{i}:v]trim=duration={clip['duration']},setpts=PTS-STARTPTS,"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},setsar=1[v{i}]"
        )
        concat_inputs.append(f"[v{i}]")

    inputs.extend(["-i", str(voiceover_path)])
    voiceover_idx = len(broll_list)

    filter_parts.append(
        "".join(concat_inputs) + f"concat=n={len(broll_list)}:v=1:a=0[vbase]"
    )

    # Subtítulos ASS
    current_label = "vbase"
    if srt_path.exists():
        ass_path = output_dir / f"{video_id}_subs.ass"
        srt_to_ass(srt_path, ass_path, cfg.get("subtitle_fontsize", 52))
        ass_escaped = str(ass_path).replace("\\", "/").replace("C:", "C\\:")
        filter_parts.append(f"[{current_label}]subtitles='{ass_escaped}'[vsubs]")
        current_label = "vsubs"

    # Overlays de texto (hook, warning, CTA)
    for i, ov in enumerate(cfg.get("overlays", [])):
        next_label = f"vtxt{i}" if i < len(cfg.get("overlays", [])) - 1 else "vfinal"
        text_escaped = ov["text"].replace("'", "\\'").replace(":", "\\:")
        filter_parts.append(
            f"[{current_label}]drawtext="
            f"text='{text_escaped}':"
            f"fontfile='{FONT_BOLD}':"
            f"fontsize={ov.get('fontsize', 64)}:"
            f"fontcolor={ov.get('color', 'white')}:"
            f"bordercolor={ov.get('bordercolor', 'black')}:"
            f"borderw={ov.get('borderw', 4)}:"
            f"x=(w-text_w)/2:"
            f"y={ov.get('y', 'h/2')}:"
            f"enable='between(t\\,{ov['t_start']}\\,{ov['t_end']})'[{next_label}]"
        )
        current_label = next_label

    # Si no hay overlays, renombrar vbase/vsubs a vfinal
    if not cfg.get("overlays"):
        filter_parts.append(f"[{current_label}]null[vfinal]")

    filter_complex = ";".join(filter_parts)
    output_path = output_dir / f"{video_id}_final.mp4"

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
        str(output_path),
    ]
    print(f"  [FFMPEG] {output_path.name}...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [FAIL] ffmpeg exit {r.returncode}")
        print(r.stderr[-2000:])
        return None
    print(f"  [OK] {output_path.name} → {output_path.stat().st_size // 1024} KB")

    # PASO 3: Thumbnail
    print("\n--- PASO 3: THUMBNAIL ---")
    thumb_path = output_dir / f"{video_id}_thumbnail.png"
    thumb_texts = cfg.get("thumbnail_texts", [])
    if not thumb_texts and cfg.get("overlays"):
        # Usar primer overlay como thumbnail text
        ov0 = cfg["overlays"][0]
        thumb_texts = [{"text": ov0["text"], "fontsize": ov0.get("fontsize", 64),
                        "color": ov0.get("color", "white"), "y": 300}]

    vf_parts = []
    for tt in thumb_texts:
        text_escaped = tt["text"].replace("'", "\\'").replace(":", "\\:")
        vf_parts.append(
            f"drawtext=text='{text_escaped}':"
            f"fontfile='{FONT_BOLD}':"
            f"fontsize={tt.get('fontsize', 64)}:"
            f"fontcolor={tt.get('color', 'white')}:"
            f"bordercolor=black:borderw=5:"
            f"x=(w-text_w)/2:y={tt.get('y', 300)}"
        )

    thumb_cmd = [
        "ffmpeg", "-y", "-i", str(output_path),
        "-ss", "0.5", "-vframes", "1",
        "-vf", ",".join(vf_parts) if vf_parts else "scale=1080:1920",
        str(thumb_path),
    ]
    r = subprocess.run(thumb_cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  [OK] {thumb_path.name}")
    else:
        print(f"  [WARN] Thumbnail fallido: {r.stderr[-500:]}")

    print(f"\n{'='*60}")
    print(f"COMPLETADO: {video_id}")
    print(f"  Video:     {output_path}")
    print(f"  Thumbnail: {thumb_path}")
    print(f"{'='*60}\n")
    return output_path


if __name__ == "__main__":
    import importlib, sys
    if len(sys.argv) < 3 or sys.argv[1] != "--config":
        print("Uso: python -m src.pipeline.auto_editor_generic --config configs/v2_bacterias.py")
        sys.exit(1)
    config_path = sys.argv[2].replace("/", ".").replace(".py", "").replace("\\", ".")
    mod = importlib.import_module(config_path)
    produce_video(mod.VIDEO_CONFIG)
