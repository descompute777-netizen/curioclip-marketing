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

    # B-roll TEMATICO de Pexels — bandera USA, courthouse, law books, small town
    # 8847274=american flag 17s | 7175146=american flag 60s | 7704860=flag 25s
    # 28122932=courthouse 15s | 16935891=courthouse 13s | 29188239=courthouse 20s
    # 8731590=law books 11s vertical | 8731589=law books 11s | 8731441=law books 14s
    # 13357730=small town america 45s
    # Voiceover V4=35.95s → broll total 36s
    "broll_plan": [
        {"seg": "0-5",   "id": "8847274",  "duration": 5.0, "desc": "Bandera USA — hook patriotico"},
        {"seg": "5-11",  "id": "28122932", "duration": 6.0, "desc": "Courthouse justicia americana"},
        {"seg": "11-17", "id": "7175146",  "duration": 6.0, "desc": "Bandera USA ondeando — leyes"},
        {"seg": "17-23", "id": "8731590",  "duration": 6.0, "desc": "Libros de leyes — Pocatello 1948"},
        {"seg": "23-29", "id": "13357730", "duration": 6.0, "desc": "Small town America — donde aplica"},
        {"seg": "29-35", "id": "16935891", "duration": 6.0, "desc": "Courthouse — cierre legal"},
        {"seg": "35-36", "id": "7704860",  "duration": 1.0, "desc": "Bandera cierre rapido"},
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
            "y": "h/2+80", "t_start": 31, "t_end": 36,
        },
    ],

    "thumbnail_texts": [
        {"text": "En este pais es ILEGAL", "fontsize": 72, "color": "white", "y": 220},
        {"text": "NO SONREIR", "fontsize": 110, "color": "red", "y": 330},
        {"text": "Pocatello, Idaho, USA", "fontsize": 50, "color": "yellow", "y": 470},
    ],

    "subtitle_fontsize": 58,
}
