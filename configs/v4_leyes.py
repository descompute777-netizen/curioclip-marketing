"""
Config V4 — "En este pais es ILEGAL no sonreir"
Sub-nicho: Pais/Cultura WTF | Hook score: 8/10 | Duracion: 45s (voiceover 35s + buffer)
Horario: Jueves 12:00 CDMX
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_02_2026-05-13_a_2026-05-19"

VIDEO_CONFIG = {
    "video_id": "V4",
    "voiceover": "V4_LeyesAbsurdas.mp3",
    "output_dir": str(SEMANA / "JUEVES" / "OUTPUT"),

    "caption_tiktok": (
        "En Pocatello, Idaho, es ILEGAL no sonreir en publico. La ley existe desde 1948. "
        "Pero hay mas leyes absurdas: en Alaska es ilegal despertar a un oso para tomarse foto, "
        "en Florida no puedes atar un cocodrilo a un hidrante. El mundo legal es un caos. "
        "#curiosidades #leyes #datoscuriosos #sabiasque #absurdo #usa #viral #historia "
        "#culturawow #WTF #CurioClip #increible #gracioso"
    ),

    # B-roll extendido a 45s — usa 3571264 (lab/ciudad) y 3129671 (galaxia/plano) ya descargados
    "broll_plan": [
        {"seg": "0-5",   "id": "3571264",  "duration": 5.0, "desc": "Ciudad personas — hook visual"},
        {"seg": "5-10",  "id": "3129671",  "duration": 5.0, "desc": "Plano amplio ciudad"},
        {"seg": "10-16", "id": "3571264",  "duration": 6.0, "desc": "Personas reaccionando ley"},
        {"seg": "16-21", "id": "3129671",  "duration": 5.0, "desc": "Mundo mapa WTF"},
        {"seg": "21-27", "id": "3571264",  "duration": 6.0, "desc": "Ley absurda Alaska"},
        {"seg": "27-32", "id": "3129671",  "duration": 5.0, "desc": "Florida cocodrilo"},
        {"seg": "32-38", "id": "3571264",  "duration": 6.0, "desc": "Mas leyes absurdas"},
        {"seg": "38-45", "id": "3129671",  "duration": 7.0, "desc": "Cierre CTA Parte 2"},
    ],

    "overlays": [
        {
            "text": "En este pais te MULTAN",
            "fontsize": 76, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 180, "t_start": 0, "t_end": 5,
        },
        {
            "text": "si NO sonries en publico",
            "fontsize": 68, "color": "red", "bordercolor": "white", "borderw": 3,
            "y": 295, "t_start": 0, "t_end": 5,
        },
        {
            "text": "Pocatello, Idaho — 1948",
            "fontsize": 56, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": "h/2", "t_start": 10, "t_end": 17,
        },
        {
            "text": "Alaska: no puedes despertar un oso",
            "fontsize": 50, "color": "cyan", "bordercolor": "black", "borderw": 3,
            "y": "h/3", "t_start": 21, "t_end": 28,
        },
        {
            "text": "Parte 2 si llegamos a 10K likes",
            "fontsize": 60, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": "h/2+80", "t_start": 38, "t_end": 45,
        },
    ],

    "thumbnail_texts": [
        {"text": "En este pais es ILEGAL", "fontsize": 72, "color": "white", "y": 220},
        {"text": "NO SONREIR", "fontsize": 110, "color": "red", "y": 330},
        {"text": "Pocatello, Idaho, USA", "fontsize": 50, "color": "yellow", "y": 470},
    ],

    "subtitle_fontsize": 52,
}
