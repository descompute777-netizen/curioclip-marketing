"""
Config V4 — "En este país es ILEGAL no sonreír"
Sub-nicho: País/Cultura WTF | Hook score: 8/10 | Duración: 20s
Horario: Jueves 12:00 CDMX
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_02_2026-05-13_a_2026-05-19"

VIDEO_CONFIG = {
    "video_id": "V4",
    "voiceover": "V4_LeyesAbsurdas.mp3",
    "output_dir": str(SEMANA / "JUEVES" / "OUTPUT"),

    # B-roll CC0 — términos: people smiling city, world map, flag USA, law gavel
    "broll_plan": [
        {"seg": "0-4",  "id": "3571264",  "duration": 4.0, "desc": "Personas en ciudad — hook"},
        {"seg": "4-8",  "id": "3129671",  "duration": 4.0, "desc": "Collage personas sonriendo"},
        {"seg": "8-13", "id": "3178847",  "duration": 5.0, "desc": "Mapa mundial pins paises"},
        {"seg": "13-17","id": "3571264",  "duration": 4.0, "desc": "Persona confundida + leyes"},
        {"seg": "17-20","id": "3129671",  "duration": 3.0, "desc": "Cierre + CTA parte 2"},
    ],

    "overlays": [
        {
            "text": "En este pais te MULTAN",
            "fontsize": 76, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 180, "t_start": 0, "t_end": 4,
        },
        {
            "text": "si NO sonries en publico",
            "fontsize": 68, "color": "red", "bordercolor": "white", "borderw": 3,
            "y": 295, "t_start": 0, "t_end": 4,
        },
        {
            "text": "Parte 2 si llegamos a 10K likes",
            "fontsize": 58, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": "h/2+60", "t_start": 16, "t_end": 20,
        },
    ],

    "thumbnail_texts": [
        {"text": "En este pais es ILEGAL", "fontsize": 72, "color": "white", "y": 220},
        {"text": "NO SONREIR", "fontsize": 110, "color": "red", "y": 330},
        {"text": "Pocatello, Idaho, USA", "fontsize": 50, "color": "yellow", "y": 470},
    ],

    "subtitle_fontsize": 50,
}
