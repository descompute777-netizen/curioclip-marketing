"""
Config V3 — "La señal de radio que NADIE puede explicar" (UVB-76)
Sub-nicho: Misterio sin resolver | Hook score: 9/10 | Duración: 28s
Horario: Miércoles 20:00 CDMX
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_02_2026-05-13_a_2026-05-19"

VIDEO_CONFIG = {
    "video_id": "V3",
    "voiceover": "V3_RadioRusa.mp3",
    "output_dir": str(SEMANA / "MIERCOLES" / "OUTPUT"),

    # B-roll CC0 — términos: radio static, russia aerial, abandoned military building, mystery
    "broll_plan": [
        {"seg": "0-4",  "id": "5177397",  "duration": 4.0, "desc": "Radio estática — hook"},
        {"seg": "4-9",  "id": "3178847",  "duration": 5.0, "desc": "Mapa Rusia edificio"},
        {"seg": "9-15", "id": "4666752",  "duration": 6.0, "desc": "Edificio abandonado misterioso"},
        {"seg": "15-21","id": "5177397",  "duration": 6.0, "desc": "Interceptación de voz"},
        {"seg": "21-25","id": "3178847",  "duration": 4.0, "desc": "Imagen satelital"},
        {"seg": "25-28","id": "5177397",  "duration": 3.0, "desc": "Pantalla negra + buzzer + CTA"},
    ],

    "overlays": [
        {
            "text": "Esta senal suena hace 50 ANOS",
            "fontsize": 72, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 180, "t_start": 0, "t_end": 4,
        },
        {
            "text": "y nadie sabe por que",
            "fontsize": 64, "color": "red", "bordercolor": "white", "borderw": 3,
            "y": 290, "t_start": 0, "t_end": 4,
        },
        {
            "text": "UVB-76 — Rusia — 1973",
            "fontsize": 52, "color": "yellow", "bordercolor": "black", "borderw": 3,
            "y": "h/2", "t_start": 9, "t_end": 15,
        },
        {
            "text": "Tu que crees que es? Comenta",
            "fontsize": 60, "color": "white", "bordercolor": "black", "borderw": 4,
            "y": "h/2+60", "t_start": 24, "t_end": 28,
        },
    ],

    "thumbnail_texts": [
        {"text": "Esta senal de radio", "fontsize": 68, "color": "white", "y": 220},
        {"text": "lleva 50 ANOS", "fontsize": 96, "color": "red", "y": 320},
        {"text": "y NADIE sabe que es", "fontsize": 62, "color": "yellow", "y": 450},
    ],

    "subtitle_fontsize": 48,
}
