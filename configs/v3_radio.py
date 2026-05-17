"""
Config V3 — "La señal de radio que NADIE puede explicar" (UVB-76)
Sub-nicho: Misterio sin resolver | Hook score: 9/10 | Duracion: 50s (voiceover 40s + buffer)
Horario: Miercoles 20:00 CDMX
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_02_2026-05-13_a_2026-05-19"

VIDEO_CONFIG = {
    "video_id": "V3",
    "voiceover": "V3_RadioRusa.mp3",
    "output_dir": str(SEMANA / "MIERCOLES" / "OUTPUT"),

    "caption_tiktok": (
        "Esta senal de radio suena desde 1973 y NADIE sabe que es ni para que sirve. "
        "La UVB-76 transmite desde Rusia y de vez en cuando da codigos misteriosos. "
        "La CIA, ex agentes, y radioaficionados llevan 50 anos sin explicarla. "
        "#curiosidades #misterio #datoscuriosos #sabiasque #rusia #enigma #conspiracion "
        "#historia #radiomisterio #CurioClip #viral #increible #ovni"
    ),

    # B-roll — solo IDs verificados como videos reales
    # 3571264=laboratorio 33s | 3129671=cosmos 40s
    # 4666752 era foto Pexels, no video — REEMPLAZADO
    # Voiceover V3=41.09s → broll total 44s (buffer 3s con -shortest)
    "broll_plan": [
        {"seg": "0-6",   "id": "3571264",  "duration": 6.0, "desc": "Laboratorio oscuro — hook misterio transmision"},
        {"seg": "6-12",  "id": "3129671",  "duration": 6.0, "desc": "Cosmos — escala del misterio"},
        {"seg": "12-18", "id": "3571264",  "duration": 6.0, "desc": "Investigacion tecnica — datos UVB-76"},
        {"seg": "18-24", "id": "3129671",  "duration": 6.0, "desc": "Espacio profundo — desconocido"},
        {"seg": "24-30", "id": "3571264",  "duration": 6.0, "desc": "Lab — analisis de la senal"},
        {"seg": "30-36", "id": "3129671",  "duration": 6.0, "desc": "Cosmos expansion — 50 anos de misterio"},
        {"seg": "36-42", "id": "3571264",  "duration": 6.0, "desc": "Cierre laboratorio — nadie lo explica"},
        {"seg": "42-44", "id": "3129671",  "duration": 2.0, "desc": "Buffer cosmos — CTA comenta"},
    ],

    "overlays": [
        {
            "text": "Esta senal suena hace 50 ANOS",
            "fontsize": 72, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 180, "t_start": 0, "t_end": 5,
        },
        {
            "text": "y nadie sabe por que",
            "fontsize": 64, "color": "red", "bordercolor": "white", "borderw": 3,
            "y": 290, "t_start": 0, "t_end": 5,
        },
        {
            "text": "UVB-76 — Rusia — 1973",
            "fontsize": 52, "color": "yellow", "bordercolor": "black", "borderw": 3,
            "y": "h/2", "t_start": 10, "t_end": 18,
        },
        {
            "text": "Incluso la CIA no pudo explicarlo",
            "fontsize": 56, "color": "cyan", "bordercolor": "black", "borderw": 4,
            "y": "h/3", "t_start": 25, "t_end": 33,
        },
        {
            "text": "Tu que crees que es? Comenta",
            "fontsize": 60, "color": "white", "bordercolor": "black", "borderw": 4,
            "y": "h/2+60", "t_start": 37, "t_end": 41,
        },
    ],

    "thumbnail_texts": [
        {"text": "Esta senal de radio", "fontsize": 68, "color": "white", "y": 220},
        {"text": "lleva 50 ANOS", "fontsize": 96, "color": "red", "y": 320},
        {"text": "y NADIE sabe que es", "fontsize": 62, "color": "yellow", "y": 450},
    ],

    "subtitle_fontsize": 58,
}
