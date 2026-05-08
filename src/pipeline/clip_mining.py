"""
Clip Mining Pipeline — CurioClip
==================================
Descarga el Golden Clip de un video viral, lo corta con ffmpeg,
genera subtítulos con Whisper, y prepara la estructura de entregables.

Uso:
    python clip_mining.py --url "https://youtube.com/..." --start 0:15 --end 0:45 --output SEMANA_01/LUNES
    python clip_mining.py --batch 20_Investigacion/viral_clips_sprint_1.md
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Asegurar que ffmpeg esté en el PATH via static-ffmpeg
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    pass  # ffmpeg ya está en PATH del sistema

VAULT = Path(__file__).parent.parent.parent / "obsidian_vault"
SEMANAS = VAULT / "SEMANAS"


def download_clip(url: str, output_dir: Path, filename: str = "source") -> Path:
    """Descarga el video fuente con yt-dlp."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{filename}.%(ext)s"
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", str(output_path),
        "--no-playlist",
        url
    ]
    print(f"[yt-dlp] Descargando: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp error: {result.stderr}")
    # Find the downloaded file
    for f in output_dir.glob(f"{filename}.*"):
        if f.suffix in {".mp4", ".mkv", ".webm"}:
            print(f"[yt-dlp] Guardado: {f}")
            return f
    raise FileNotFoundError("yt-dlp no encontró el archivo descargado")


def cut_golden_clip(input_path: Path, start: str, end: str, output_path: Path) -> Path:
    """Corta el Golden Clip con ffmpeg usando timestamps HH:MM:SS o MM:SS."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-ss", start,
        "-to", end,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        str(output_path)
    ]
    print(f"[ffmpeg] Cortando {start} → {end}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr[-500:]}")
    print(f"[ffmpeg] Golden clip: {output_path}")
    return output_path


def generate_subtitles(video_path: Path, language: str = "es") -> Path:
    """Genera subtítulos .srt con OpenAI Whisper."""
    try:
        import whisper
    except ImportError:
        print("[whisper] No instalado. Instalar con: pip install openai-whisper")
        return None

    print(f"[whisper] Transcribiendo en {language}...")
    model = whisper.load_model("base")
    result = model.transcribe(str(video_path), language=language, task="transcribe")

    srt_path = video_path.with_suffix(".srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], 1):
            start = _seconds_to_srt(seg["start"])
            end = _seconds_to_srt(seg["end"])
            f.write(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n\n")

    print(f"[whisper] Subtítulos: {srt_path}")
    return srt_path


def _seconds_to_srt(seconds: float) -> str:
    """Convierte segundos a formato SRT HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def create_deliverable_structure(output_dir: Path, url: str, start: str, end: str, hook: str = "") -> None:
    """Crea la estructura de archivos de entregable para el clip."""
    source_dir = output_dir / "SOURCE"
    output_files_dir = output_dir / "OUTPUT"
    source_dir.mkdir(parents=True, exist_ok=True)
    output_files_dir.mkdir(parents=True, exist_ok=True)

    # source_url.txt
    (source_dir / "source_url.txt").write_text(url, encoding="utf-8")

    # golden_clip_timestamps.txt
    (source_dir / "golden_clip_timestamps.txt").write_text(
        f"INICIO: {start}\nFIN: {end}\nDURACIÓN: ~{_calc_duration(start, end)}s\n",
        encoding="utf-8"
    )

    # compliance_check.md (template)
    compliance = f"""---
agente: A9_Compliance
fecha: {datetime.now().strftime('%Y-%m-%d')}
tags: [compliance, clip-mining]
estado: pendiente
---
# Compliance Check — Clip Mining

**URL fuente:** {url}
**Golden Clip:** {start} → {end}

## Verificación de Licencia
- [ ] Licencia verificada: [ ] CC-BY  [ ] CC-BY-SA  [ ] Dominio Público  [ ] Fair Use
- [ ] Transformación aplicada (subtítulos + overlay + contexto): [ ] Sí  [ ] No
- [ ] Duración del clip ≤30s para Fair Use: [ ] Sí  [ ] No (duración: ~{_calc_duration(start, end)}s)
- [ ] Crédito al creador incluido en caption: [ ] Sí  [ ] No

**DECISIÓN:** [ ] APROBADO  [ ] RECHAZADO

**Justificación:** _______________
"""
    (source_dir / "compliance_check.md").write_text(compliance, encoding="utf-8")

    # caption templates
    hook_text = hook or "[HOOK — escribir texto de apertura]"
    (output_files_dir / "caption_tiktok.txt").write_text(
        f"{hook_text}\n\n[Dato sorprendente en 1-2 frases]\n\n"
        f"¿Lo sabías? 👇 Sígueme para más 🧠\n\n"
        f"Vía: @[usuario_original]\n\n"
        f"#datoscuriosos #sabiasque #ciencia #curioclip #curiosidades",
        encoding="utf-8"
    )
    (output_files_dir / "caption_facebook.txt").write_text(
        f"{hook_text}\n\n"
        f"[Contexto más amplio del dato — 3-4 frases para Facebook]\n\n"
        f"¿Conocías este dato? Déjanos tu comentario 👇\n\n"
        f"Contenido vía @[usuario_original] | CurioClip\n\n"
        f"#datoscuriosos #sabiasque #curiosidades",
        encoding="utf-8"
    )
    (output_files_dir / "hashtags_tiktok.txt").write_text(
        "#datoscuriosos #sabiasque #ciencia #curioclip #curiosidades #cienciaentiktok #aprendeentiktok",
        encoding="utf-8"
    )
    (output_files_dir / "hashtags_facebook.txt").write_text(
        "#datoscuriosos #curiosidades #ciencia",
        encoding="utf-8"
    )

    # brief_visual.md
    (output_dir / "brief_visual.md").write_text(
        f"""---
agente: A4_Editor
fecha: {datetime.now().strftime('%Y-%m-%d')}
---
# Brief Visual — Clip Mining

## Video fuente
- URL: {url}
- Golden Clip: {start} → {end}

## Hook overlay (0-3s)
Texto grande centrado, mitad superior del frame:
**"{hook_text}"**
- Fuente: Bold, ≥50px
- Color: Blanco o Amarillo sobre fondo oscuro
- Animación: entrada rápida (0.2s fade-in)

## Subtítulos
- Posición: bottom center
- Color: Blanco con sombra negra
- Fuente: Bold, 24-28px
- Importar .srt generado por Whisper

## Música
- Baja en primeros 3s (para que se escuche el audio del clip)
- Subir gradualmente después del hook
- Fuente: Pixabay Music (royalty-free)

## Cierre (últimos 2s)
- Logo CurioClip bottom right
- CTA: "Sígueme para más 🧠" o "¿Lo sabías? 👇"

## Exportar
- Formato: MP4, 9:16, 1080x1920, 30fps
- Destino: OUTPUT/golden_clip_final.mp4

## Thumbnail (OBLIGATORIO — Canva MCP)
- Capturar el frame más impactante del clip
- Añadir texto del hook en grande
- Colores: fondo oscuro, texto blanco/amarillo, acento rojo/naranja
- Guardar como: OUTPUT/thumbnail.png
""",
        encoding="utf-8"
    )

    print(f"[estructura] Entregables creados en: {output_dir}")


def _calc_duration(start: str, end: str) -> int:
    """Calcula duración aproximada en segundos entre dos timestamps MM:SS."""
    def to_seconds(ts):
        parts = ts.replace(",", ".").split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    try:
        return int(to_seconds(end) - to_seconds(start))
    except Exception:
        return 0


def process_single(url: str, start: str, end: str, output_dir: str, hook: str = "") -> None:
    """Pipeline completo para un solo clip."""
    out = Path(output_dir)
    source_dir = out / "SOURCE"

    print(f"\n{'='*60}")
    print(f"CLIP MINING — {url}")
    print(f"Golden Clip: {start} → {end}")
    print(f"{'='*60}\n")

    # 1. Crear estructura
    create_deliverable_structure(out, url, start, end, hook)

    # 2. Descargar
    try:
        source_path = download_clip(url, source_dir, "source")
    except Exception as e:
        print(f"[ERROR] Descarga fallida: {e}\nVerificar licencia y disponibilidad.")
        return

    # 3. Cortar Golden Clip
    raw_clip = out / "SOURCE" / "golden_clip_raw.mp4"
    try:
        cut_golden_clip(source_path, start, end, raw_clip)
    except Exception as e:
        print(f"[ERROR] Corte fallido: {e}")
        return

    # 4. Subtítulos
    srt_path = generate_subtitles(raw_clip)
    if srt_path:
        import shutil
        shutil.copy(srt_path, out / "OUTPUT" / "subtitles_es.srt")

    print(f"\n✅ Pipeline completo. Entregables en: {out}")
    print("📋 Próximo paso: abrir en CapCut → añadir overlay hook + subtítulos .srt → exportar")
    print("🖼️  Generar thumbnail vía Canva MCP → guardar en OUTPUT/thumbnail.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CurioClip Clip Mining Pipeline")
    parser.add_argument("--url", required=True, help="URL del video fuente")
    parser.add_argument("--start", required=True, help="Timestamp inicio Golden Clip (MM:SS o HH:MM:SS)")
    parser.add_argument("--end", required=True, help="Timestamp fin Golden Clip (MM:SS o HH:MM:SS)")
    parser.add_argument("--output", required=True, help="Directorio de salida (ej: obsidian_vault/SEMANAS/SEMANA_01/LUNES)")
    parser.add_argument("--hook", default="", help="Texto del hook para el overlay (0-3s)")
    args = parser.parse_args()

    process_single(args.url, args.start, args.end, args.output, args.hook)
