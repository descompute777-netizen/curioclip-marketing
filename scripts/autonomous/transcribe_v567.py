"""Transcribe V5/V6/V7 MP3s to SRT with Whisper."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import static_ffmpeg
static_ffmpeg.add_paths()
import whisper
from pathlib import Path

AUDIO_DIR = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING\obsidian_vault\30_Contenido\audios_generados")

MP3S = ["V5_Tunguska.mp3", "V6_Conan.mp3", "V7_Cosquillas.mp3"]


def s2srt(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60); ms = int((s % 1) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


print("[WHISPER] Cargando modelo base (esp)...")
model = whisper.load_model("base")

for name in MP3S:
    mp3 = AUDIO_DIR / name
    if not mp3.exists():
        print(f"[SKIP] {name} no existe")
        continue
    print(f"\n[WHISPER] Transcribiendo {name}...")
    r = model.transcribe(str(mp3), language="es", task="transcribe", verbose=False)
    srt = AUDIO_DIR / name.replace(".mp3", ".srt")
    with open(srt, "w", encoding="utf-8") as f:
        for i, seg in enumerate(r["segments"], 1):
            f.write(f"{i}\n{s2srt(seg['start'])} --> {s2srt(seg['end'])}\n{seg['text'].strip()}\n\n")
    print(f"[OK] {srt.name} | {len(r['segments'])} segs | {r['segments'][-1]['end']:.1f}s total")
