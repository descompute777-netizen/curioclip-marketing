"""
Higgsfield AI Video MCP Wrapper
================================
Generacion de video AI con 30+ modelos.
URL: https://higgsfield.ai
Lanzado: Abril 2026 | VERIFICADO: Mayo 2026 — REAL.

Capacidades:
  - Text-to-video: generar clips desde prompt de texto
  - Image-to-video: animar imagenes estaticas
  - Video effects: efectos cinematograficos AI
  - Ideal para: B-roll, transiciones, clips de concepto para M3 PRODUCE

REQUISITO: API key de higgsfield.ai/pricing
FALLBACK si no disponible: CapCut (manual, gratis) o FFmpeg (script)

MODULO PIPELINE: M3 PRODUCE
"""

import os
import json
import time
import requests
from typing import Optional


HIGGSFIELD_API_KEY = os.environ.get("HIGGSFIELD_API_KEY", "<<<PENDIENTE>>>")
HIGGSFIELD_BASE = "https://api.higgsfield.ai"


class HiggsfieldClient:
    """Cliente para Higgsfield AI Video Generation."""

    def __init__(self, api_key: str = HIGGSFIELD_API_KEY):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def _not_configured(self) -> Optional[dict]:
        if self.api_key == "<<<PENDIENTE>>>":
            return {
                "error": "Higgsfield API key no configurada.",
                "accion": "Ir a higgsfield.ai → crear cuenta → obtener API key",
                "env": "Agregar HIGGSFIELD_API_KEY=hf_... al .env",
                "fallback": "Usar CapCut (gratis, manual) o generar script FFmpeg",
                "status": "REAL — verificado mayo 2026"
            }
        return None

    def generate_from_text(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        style: str = "cinematic",
        negative_prompt: str = ""
    ) -> dict:
        """
        Genera un clip de video desde un prompt de texto.

        Args:
            prompt: Descripcion del video (ej: "medusa brillante en oceano oscuro, slow motion").
            duration: Duracion en segundos (tipicamente 3-8s para clips de hook).
            aspect_ratio: "9:16" para TikTok/Reels, "16:9" para YouTube.
            style: Estilo visual — cinematic, realistic, anime, cartoon, etc.
            negative_prompt: Que evitar en el video.

        Uso en pipeline: M3 PRODUCE para generar B-roll o clips de concepto.
        """
        err = self._not_configured()
        if err:
            return err

        resp = self.session.post(
            f"{HIGGSFIELD_BASE}/v1/generate",
            json={
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "style": style,
                "negative_prompt": negative_prompt
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()

    def animate_image(
        self,
        image_url: str,
        motion_prompt: str,
        duration: int = 4,
        motion_intensity: str = "medium"
    ) -> dict:
        """
        Anima una imagen estatica con movimiento AI.

        Args:
            image_url: URL de la imagen de entrada (Pexels, Unsplash — royalty free).
            motion_prompt: Descripcion del movimiento (ej: "slow zoom in, particles floating").
            duration: Duracion en segundos.
            motion_intensity: "low" | "medium" | "high"

        Uso: convertir imagenes de Pexels en clips animados para el video.
        """
        err = self._not_configured()
        if err:
            return err

        resp = self.session.post(
            f"{HIGGSFIELD_BASE}/v1/image-to-video",
            json={
                "image_url": image_url,
                "prompt": motion_prompt,
                "duration": duration,
                "motion_intensity": motion_intensity
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()

    def get_generation_status(self, generation_id: str) -> dict:
        """Verifica el estado de una generacion en progreso."""
        err = self._not_configured()
        if err:
            return err

        resp = self.session.get(
            f"{HIGGSFIELD_BASE}/v1/generations/{generation_id}",
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def wait_for_completion(self, generation_id: str,
                            poll_interval: int = 5, max_wait: int = 300) -> dict:
        """Poll hasta que la generacion termine."""
        elapsed = 0
        while elapsed < max_wait:
            status = self.get_generation_status(generation_id)
            if status.get("status") in ("completed", "failed"):
                return status
            time.sleep(poll_interval)
            elapsed += poll_interval
        return {"status": "timeout", "generation_id": generation_id}

    def health_check(self) -> dict:
        if self.api_key == "<<<PENDIENTE>>>":
            return {
                "status": "not_configured",
                "herramienta": "Higgsfield AI Video",
                "url": "https://higgsfield.ai",
                "lanzado": "Abril 2026",
                "verificado": "Mayo 2026 — REAL",
                "fallback": "CapCut (gratis, manual) es la alternativa sin costo",
                "uso_pipeline": "M3 PRODUCE — generacion de B-roll y clips de concepto"
            }
        return {"status": "configured", "url": HIGGSFIELD_BASE}


def generate_ffmpeg_script(
    input_files: list,
    output_path: str,
    aspect_ratio: str = "9:16",
    add_subtitles: bool = True
) -> str:
    """
    Genera un script FFmpeg para procesamiento de video sin API.
    Alternativa gratuita y local a Higgsfield.

    Args:
        input_files: Lista de archivos de entrada (videos, imagenes).
        output_path: Ruta del video de salida.
        aspect_ratio: "9:16" para TikTok.
        add_subtitles: Si agregar subtitulos (requiere archivo .srt).

    Returns:
        String con el comando FFmpeg listo para ejecutar.
    """
    if aspect_ratio == "9:16":
        scale_filter = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
    else:
        scale_filter = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"

    input_str = " ".join(f"-i {f}" for f in input_files)

    script = f"""# Script FFmpeg — generado por M3 PRODUCE
# Requiere FFmpeg instalado: https://ffmpeg.org/download.html

ffmpeg {input_str} \\
  -filter_complex "[0:v]{scale_filter}[v]" \\
  -map "[v]" -map 0:a? \\
  -c:v libx264 -crf 18 -preset slow \\
  -c:a aac -b:a 192k \\
  -movflags +faststart \\
  {output_path}

# Para agregar subtitulos (archivo .srt):
# ffmpeg -i {output_path} -vf "subtitles=subtitles.srt:force_style='FontSize=24,PrimaryColour=&Hffffff,Bold=1'" output_con_subs.mp4
"""
    return script


MCP_TOOLS_SCHEMA = {
    "server_name": "higgsfield-mcp",
    "description": "Higgsfield AI Video — 30+ modelos. Lanzado abril 2026. REAL.",
    "url": "https://higgsfield.ai",
    "modulo_pipeline": "M3_PRODUCE",
    "tools": [
        {"name": "generate_from_text", "desc": "Text-to-video para B-roll y clips de concepto"},
        {"name": "animate_image", "desc": "Image-to-video para animar fotos de Pexels/Unsplash"},
        {"name": "get_generation_status", "desc": "Status de generacion en progreso"},
    ],
    "fallbacks": {
        "CapCut": "capcut.com — gratis, manual, subtitulos automaticos en espanol",
        "FFmpeg": "open source, genera script con generate_ffmpeg_script()",
        "DaVinci Resolve": "blackmagicdesign.com/products/davinciresolve — gratis, profesional"
    }
}


if __name__ == "__main__":
    client = HiggsfieldClient()
    health = client.health_check()
    print(f"Higgsfield: {health['status']}")

    # Ejemplo de script FFmpeg alternativo
    script = generate_ffmpeg_script(
        input_files=["clip_base.mp4"],
        output_path="curioclip_v5_final.mp4",
        aspect_ratio="9:16"
    )
    print("\nScript FFmpeg de ejemplo:")
    print(script)
