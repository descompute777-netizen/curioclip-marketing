"""Genera thumbnail limpio de V5 desde el B-roll fuente (sin subs ni hook overlay del video final)."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import static_ffmpeg
static_ffmpeg.add_paths()
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SRC = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_01_2026-05-06_a_2026-05-12" / "VIERNES" / "SOURCE" / "broll_5121751.mp4"
OUT = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_01_2026-05-06_a_2026-05-12" / "VIERNES" / "OUTPUT" / "V5_thumbnail.png"

# Extract frame at 1.5s from source, scale to 1080x1920, add thumbnail text
cmd = [
    "ffmpeg", "-y", "-ss", "1.5", "-i", str(SRC),
    "-vframes", "1",
    "-vf",
    "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "drawtext=text='METIO SU MANO EN':fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
    "fontsize=78:fontcolor=white:bordercolor=black:borderw=5:"
    "x=(w-text_w)/2:y=350,"
    "drawtext=text='PLOMO FUNDIDO':fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
    "fontsize=110:fontcolor=yellow:bordercolor=black:borderw=6:"
    "x=(w-text_w)/2:y=460,"
    "drawtext=text='327 GRADOS':fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
    "fontsize=92:fontcolor='#FF3B3B':bordercolor=white:borderw=4:"
    "x=(w-text_w)/2:y=600",
    str(OUT),
]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode == 0:
    print(f"[OK] Thumbnail limpio: {OUT}")
    print(f"     Tamano: {OUT.stat().st_size//1024} KB")
else:
    print("[FAIL]", r.stderr[-1500:])
