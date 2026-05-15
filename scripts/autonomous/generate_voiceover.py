"""
Generador de Voiceover — edge-tts (GRATIS, sin API key)
=========================================================
Usa Microsoft Edge TTS para generar voiceovers en español de alta calidad.
Voces disponibles (mejores para el nicho curiosidades):
  - es-MX-JorgeNeural      (hombre, México — RECOMENDADO para CurioClip)
  - es-MX-DaliaNeural      (mujer, México)
  - es-ES-AlvaroNeural     (hombre, España)
  - es-AR-TomasNeural      (hombre, Argentina)

Uso desde CLI:
  python scripts/autonomous/generate_voiceover.py --text "Tu cuerpo..." --out voice.mp3
  python scripts/autonomous/generate_voiceover.py --script guion.md --out voice.mp3
  python scripts/autonomous/generate_voiceover.py --guion-id G01 --sprint 2

Uso desde Python:
  from scripts.autonomous.generate_voiceover import generate_voiceover
  generate_voiceover("Tu cuerpo tiene 38 billones de bacterias", "out.mp3")
"""
import os, sys, asyncio, argparse, re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
AUDIO_DIR = VAULT / "30_Contenido" / "audios_generados"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

VOICE = "es-MX-JorgeNeural"  # Mejor voz para el tono "asombroso y directo" de CurioClip
RATE = "+10%"                  # Ligera aceleración para ritmo de curiosidades
PITCH = "+0Hz"


def ensure_edge_tts():
    try:
        import edge_tts
    except ImportError:
        print("[INSTALL] pip install edge-tts")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts", "-q"], check=True)
        import edge_tts
    return edge_tts


async def _generate_async(text: str, output_path: Path, voice: str = VOICE,
                           rate: str = RATE, pitch: str = PITCH):
    edge_tts = ensure_edge_tts()
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(str(output_path))


def generate_voiceover(text: str, output_path: str | Path, voice: str = VOICE) -> Path:
    """
    Genera MP3 desde texto usando edge-tts (gratis, sin API key).
    Retorna el Path del archivo generado.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Limpiar texto para TTS (remover markdown, emojis problemáticos)
    clean_text = re.sub(r'\*+', '', text)       # negrita
    clean_text = re.sub(r'#+\s*', '', clean_text)  # headers
    clean_text = re.sub(r'\[.*?\]\(.*?\)', '', clean_text)  # links
    clean_text = re.sub(r'[^\w\s\.,;:¿?¡!áéíóúñüÁÉÍÓÚÑÜ%°]', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    print(f"[TTS] Generando voiceover ({len(clean_text)} chars) → {output_path.name}")
    asyncio.run(_generate_async(clean_text, output_path, voice))
    size_kb = output_path.stat().st_size // 1024 if output_path.exists() else 0
    print(f"[OK] {output_path.name} — {size_kb} KB")
    return output_path


def extract_script_text(guion_file: Path) -> str:
    """Extrae solo el voiceover/narración de un archivo de guión markdown."""
    text = guion_file.read_text(encoding="utf-8")

    # Extraer bloques específicos del guión
    narration_parts = []
    current_block = []
    in_block = False

    for line in text.splitlines():
        line = line.strip()
        if any(kw in line.upper() for kw in ["**HOOK", "**IDENTIFICACIÓN", "**PROMESA",
                                               "**DESARROLLO", "**CTA", "**VOICEOVER"]):
            in_block = True
            if current_block:
                narration_parts.append(" ".join(current_block))
            current_block = []
        elif in_block and line and not line.startswith("#") and not line.startswith("|"):
            # Limpiar el texto del guión (quitar marcado markdown)
            cleaned = re.sub(r'^>\s*"?|"?$', '', line.strip())
            cleaned = re.sub(r'\*\*.*?\*\*:', '', cleaned)  # headers en negrita
            if cleaned:
                current_block.append(cleaned)

    if current_block:
        narration_parts.append(" ".join(current_block))

    if not narration_parts:
        # Fallback: extraer todo el texto entre comillas o después de ">"
        narration_parts = re.findall(r'> "([^"]+)"', text)
        if not narration_parts:
            # Último recurso: tomar el texto completo limpiando markdown
            narration_parts = [re.sub(r'[#*>\[\]|]', '', text)]

    return " ".join(narration_parts)


def main():
    parser = argparse.ArgumentParser(description="Genera voiceover con edge-tts (gratis)")
    parser.add_argument("--text", help="Texto a convertir a voz")
    parser.add_argument("--script", help="Archivo .md con el guión")
    parser.add_argument("--out", help="Archivo de salida MP3")
    parser.add_argument("--voice", default=VOICE, help=f"Voz edge-tts (default: {VOICE})")
    parser.add_argument("--guion-id", help="ID del guión (ej: G01) para buscar en vault")
    parser.add_argument("--sprint", type=int, help="Número de sprint para buscar guión")
    args = parser.parse_args()

    if args.text:
        out = Path(args.out) if args.out else AUDIO_DIR / "voiceover_test.mp3"
        generate_voiceover(args.text, out, args.voice)

    elif args.script:
        script_path = Path(args.script)
        text = extract_script_text(script_path)
        out = Path(args.out) if args.out else AUDIO_DIR / f"{script_path.stem}.mp3"
        generate_voiceover(text, out, args.voice)

    else:
        # Demo con texto de ejemplo
        demo_text = (
            "Napoleón Bonaparte, el mejor estratega militar de su era, fue derrotado en batalla "
            "por conejos. Y no es metáfora. Pasó de verdad. Julio de 1807. Tres días después de "
            "firmar el Tratado de Tilsit. ¿Quieres saber los otros dos hechos más absurdos de esa semana?"
        )
        out = AUDIO_DIR / "demo_voiceover.mp3"
        generate_voiceover(demo_text, out)
        print(f"\n[DEMO] Voiceover generado: {out}")
        print("  Reproduce con: start demo_voiceover.mp3")


if __name__ == "__main__":
    main()
