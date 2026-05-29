"""
tts_elevenlabs.py — Voz cálida/humana vía ElevenLabs (reemplaza edge-tts).
=============================================================================
ElevenLabs = la voz más natural disponible. Tier gratis: ~10k chars/mes.

Setup (1 vez):
  1. Crea cuenta en https://elevenlabs.io  (gratis)
  2. Profile → API Key → copia
  3. Pégala en .env →  ELEVENLABS_API_KEY=sk_...   y   TTS_PROVIDER=elevenlabs

Uso:
  python scripts/autonomous/tts_elevenlabs.py --voices          # lista tus voces
  python scripts/autonomous/tts_elevenlabs.py --samples         # genera comparativa
  # programático:
  from scripts.autonomous.tts_elevenlabs import synth
  synth("texto", Path("out.mp3"), voice_id="...")
"""
from __future__ import annotations
import os, sys, json, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

API = "https://api.elevenlabs.io/v1"
# eleven_multilingual_v2 = alta calidad + español nativo. (turbo/flash = más rápido/barato)
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# Ajustes para CALIDEZ: algo de expresividad (stability media), timbre consistente.
WARM_SETTINGS = {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35,
                 "use_speaker_boost": True}

SAMPLE = ("¿Qué pasaría si pudieras sostener una cucharada de estrella muerta? "
          "Pesaría más que el monte Everest. Es lo más denso del universo entero.")


def _key() -> str:
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not k or k.startswith("<<<"):
        sys.exit("[FALTA] Pega tu key en .env → ELEVENLABS_API_KEY=sk_...  "
                 "(gratis en https://elevenlabs.io → Profile → API Key)")
    return k


def list_voices() -> list[dict]:
    req = urllib.request.Request(f"{API}/voices", headers={"xi-api-key": _key()})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    return data.get("voices", [])


def synth(text: str, out_path: Path, voice_id: str, model: str = MODEL) -> Path:
    """Genera MP3 con ElevenLabs. Devuelve el Path."""
    out_path = Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({
        "text": text, "model_id": model, "voice_settings": WARM_SETTINGS,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{API}/text-to-speech/{voice_id}", data=body, method="POST",
        headers={"xi-api-key": _key(), "Content-Type": "application/json",
                 "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out_path.write_bytes(r.read())
    return out_path


# Voces premade de ElevenLabs que suenan cálidas y rinden bien en español.
# (Si no están en tu cuenta, --samples usa las que tengas disponibles.)
PREFERRED = [
    ("Sarah_f",  "EXAVITQu4vr4xnSDxMaL"),   # cálida femenina
    ("Antoni_m", "ErXwobaYiN019PkySvjV"),   # cálido masculino
    ("Charlie_m","IKne3meq5aSn9XLyUdCD"),   # natural, cercano
    ("Matilda_f","XrExE9yKIg1WjnnlVkGX"),   # suave femenina
]


def generate_samples():
    out = ROOT / "voice_samples"; out.mkdir(exist_ok=True)
    # descubrir voces reales de la cuenta
    try:
        mine = list_voices()
        avail = {v["voice_id"]: v["name"] for v in mine}
        print(f"[INFO] {len(avail)} voces en tu cuenta")
    except Exception as e:
        print(f"[WARN] no pude listar voces ({e}); intento con las premade")
        avail = {}
    targets = [(n, vid) for n, vid in PREFERRED if not avail or vid in avail]
    if not targets and avail:  # usar las primeras 4 de la cuenta
        targets = [(f"{name.replace(' ','')}", vid) for vid, name in list(avail.items())[:4]]
    ok = 0
    for name, vid in targets:
        try:
            dest = synth(SAMPLE, out / f"eleven_{name}.mp3", vid)
            print(f"[OK] eleven_{name} -> {dest.stat().st_size//1024} KB  (voice_id={vid})")
            ok += 1
        except Exception as e:
            err = e.read()[:160] if hasattr(e, "read") else str(e)[:160]
            print(f"[FAIL] {name}: {err}")
    print(f"\n[OK] {ok} muestras en {out}. Escucha y dime cuál — luego la cableo al pipeline.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--voices" in args:
        for v in list_voices():
            labels = v.get("labels", {})
            print(f"  {v['name']:18s} {v['voice_id']}  {labels.get('accent','')}/{labels.get('description','')}")
    elif "--samples" in args:
        generate_samples()
    else:
        print(__doc__)
