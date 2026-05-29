"""
voice_compare.py — Genera el MISMO texto en varias voces/motores para elegir.
Salida: voice_samples/*.mp3|wav  + manifest. Reproduce y elige la que más natural suene.

Motores:
  - edge-tts (gratis): mejores voces ES a ritmo NATURAL (+0%, no +10%).
  - Gemini TTS (gemini-2.5-flash-preview-tts): mucho más natural, vía REST.
"""
from __future__ import annotations
import os, sys, asyncio, base64, json, struct, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "voice_samples"
OUT.mkdir(exist_ok=True)

# cargar .env
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

SAMPLE = ("¿Qué pasaría si pudieras sostener una cucharada de estrella muerta? "
          "Pesaría más que el monte Everest. Es lo más denso del universo entero.")

# Voces edge curadas (variedad M/F + acentos), a ritmo natural
EDGE_VOICES = [
    ("edge_MX_Jorge_m",   "es-MX-JorgeNeural",  "+0%", "+0Hz"),
    ("edge_US_Alonso_m",  "es-US-AlonsoNeural", "+0%", "+0Hz"),
    ("edge_MX_Dalia_f",   "es-MX-DaliaNeural",  "+0%", "+0Hz"),
    ("edge_CO_Gonzalo_m", "es-CO-GonzaloNeural","+0%", "+0Hz"),
    ("edge_DO_Emilio_m",  "es-DO-EmilioNeural", "+0%", "+0Hz"),   # acento dominicano
    ("edge_ES_Alvaro_m",  "es-ES-AlvaroNeural", "+0%", "+0Hz"),
]

# Gemini TTS — voces prebuilt (m/f, distintos timbres)
GEMINI_VOICES = [
    ("gemini_Charon_m", "Charon"),   # grave, informativo
    ("gemini_Puck_m",   "Puck"),     # animado/upbeat
    ("gemini_Kore_f",   "Kore"),     # firme femenina
    ("gemini_Fenrir_m", "Fenrir"),   # energético
]


async def _edge_one(name, voice, rate, pitch):
    import edge_tts
    dest = OUT / f"{name}.mp3"
    await edge_tts.Communicate(SAMPLE, voice=voice, rate=rate, pitch=pitch).save(str(dest))
    print(f"[edge] {name:18s} -> {dest.name} ({dest.stat().st_size//1024} KB)")


def gen_edge():
    for name, voice, rate, pitch in EDGE_VOICES:
        try:
            asyncio.run(_edge_one(name, voice, rate, pitch))
        except Exception as e:
            print(f"[edge] {name} FALLO: {e}")


def _pcm_to_wav(pcm: bytes, rate=24000, ch=1, bits=16) -> bytes:
    byte_rate = rate * ch * bits // 8
    block = ch * bits // 8
    return (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE" + b"fmt " +
            struct.pack("<IHHIIHH", 16, 1, ch, rate, byte_rate, block, bits) +
            b"data" + struct.pack("<I", len(pcm)) + pcm)


def gen_gemini():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("[gemini] sin GEMINI_API_KEY"); return
    model = "gemini-2.5-flash-preview-tts"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    for name, voice in GEMINI_VOICES:
        body = {
            "contents": [{"parts": [{"text": SAMPLE}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
            },
        }
        try:
            req = urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read())
            b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
            pcm = base64.b64decode(b64)
            dest = OUT / f"{name}.wav"
            dest.write_bytes(_pcm_to_wav(pcm))
            print(f"[gemini] {name:18s} -> {dest.name} ({dest.stat().st_size//1024} KB)")
        except Exception as e:
            msg = getattr(e, "read", lambda: b"")() if hasattr(e, "read") else b""
            print(f"[gemini] {name} FALLO: {e} {msg[:200]}")


if __name__ == "__main__":
    print(f"Texto de muestra:\n  \"{SAMPLE}\"\n")
    gen_edge()
    gen_gemini()
    print(f"\n[OK] Muestras en: {OUT}")
    print("Reproduce y dime cuál te gusta (nombre del archivo).")
