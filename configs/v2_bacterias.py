"""
Config V2 — "Tu cuerpo tiene más bacterias que estrellas en la galaxia"
Sub-nicho: Comparación imposible | Hook score: 9/10 | Duración: 18s
Horario: Lunes 12:00 CDMX
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_02_2026-05-13_a_2026-05-19"

VIDEO_CONFIG = {
    "video_id": "V2",
    "voiceover": "V2_Bacterias.mp3",
    "output_dir": str(SEMANA / "LUNES" / "OUTPUT"),

    # B-roll CC0 — términos: galaxy milky way, bacteria microscope, human body cells
    "broll_plan": [
        {"seg": "0-3",  "id": "3129671",  "duration": 3.0, "desc": "Vía Láctea — hook visual"},
        {"seg": "3-7",  "id": "5377700",  "duration": 4.0, "desc": "Bacteria microscópio animación"},
        {"seg": "7-12", "id": "3214460",  "duration": 5.0, "desc": "Cuerpo humano células"},
        {"seg": "12-15","id": "3129671",  "duration": 3.0, "desc": "Galaxia zoom dramático"},
        {"seg": "15-18","id": "5377700",  "duration": 3.0, "desc": "Cierre + CTA"},
    ],

    "overlays": [
        {
            "text": "Tu cuerpo vs la GALAXIA",
            "fontsize": 82, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 180, "t_start": 0, "t_end": 3,
        },
        {
            "text": "38 BILLONES de bacterias",
            "fontsize": 72, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": 300, "t_start": 3, "t_end": 7,
        },
        {
            "text": "Que otro dato quieres saber?",
            "fontsize": 56, "color": "white", "bordercolor": "black", "borderw": 3,
            "y": "h/2+100", "t_start": 14, "t_end": 18,
        },
    ],

    "thumbnail_texts": [
        {"text": "Tu cuerpo vs", "fontsize": 72, "color": "white", "y": 220},
        {"text": "la GALAXIA", "fontsize": 110, "color": "yellow", "y": 320},
        {"text": "38 BILLONES de bacterias", "fontsize": 52, "color": "red", "y": 460},
    ],

    "subtitle_fontsize": 50,
}
