"""Transcribe V5_PlomoFundido.mp3 with Whisper to SRT."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import static_ffmpeg
static_ffmpeg.add_paths()
import whisper

print("Cargando modelo whisper base...")
m = whisper.load_model("base")
print("Transcribiendo V5_PlomoFundido.mp3...")
r = m.transcribe(
    "obsidian_vault/30_Contenido/audios_generados/V5_PlomoFundido.mp3",
    language="es",
    task="transcribe",
    verbose=False,
)


def s2srt(s):
    h = int(s // 3600)
    m_ = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int((s % 1) * 1000)
    return f"{h:02d}:{m_:02d}:{sec:02d},{ms:03d}"


srt_path = "obsidian_vault/30_Contenido/audios_generados/V5_PlomoFundido.srt"
with open(srt_path, "w", encoding="utf-8") as f:
    for i, seg in enumerate(r["segments"], 1):
        f.write(f"{i}\n{s2srt(seg['start'])} --> {s2srt(seg['end'])}\n{seg['text'].strip()}\n\n")

print(f"\n[OK] SRT guardado en: {srt_path}")
print(f"[OK] Segmentos: {len(r['segments'])}")
print(f"[OK] Duracion total: {r['segments'][-1]['end']:.1f}s")
print()
print("=== TRANSCRIPCION COMPLETA ===")
print(r["text"])
