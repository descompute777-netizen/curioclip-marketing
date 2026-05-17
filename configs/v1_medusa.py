"""
Config V1 — "El animal que NO puede morir" (Medusa Turritopsis dohrnii)
Sub-nicho: ¿Sabías que...? | Hook score: 8/10 | Duración: 22s
Horario: Martes 19:00 CDMX
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_02_2026-05-13_a_2026-05-19"

VIDEO_CONFIG = {
    "video_id": "V1",
    "voiceover": "V1_Medusa.mp3",
    "output_dir": str(SEMANA / "MARTES" / "OUTPUT"),

    # Caption para TikTok
    "caption_tiktok": (
        "Este animal puede REVERTIR su envejecimiento y volver a ser joven infinitamente. "
        "La Turritopsis dohrnii es el unico ser vivo biologicamente inmortal conocido. "
        "La ciencia aun no sabe como replicarlo en humanos. "
        "#curiosidades #datoscuriosos #sabiasque #ciencia #biologia #inmortal #medusa "
        "#naturaleza #animal #CurioClip #viral #increible"
    ),

    # B-roll TEMATICO de Pexels — videos REALES de medusas verificados via broll_finder.py
    # 28635601=jellyfish ocean 14s | 13320123=medusa bioluminiscente 60s vertical
    # 16521053=jellyfish ocean 39s | 12210147=deep sea creature 22s
    # 8950635=jellyfish glowing 11s | 2840467=jellyfish bioluminiscente 18s
    "broll_plan": [
        {"seg": "0-5",   "id": "28635601", "duration": 5.0, "desc": "Medusa oceano — hook inmortal"},
        {"seg": "5-11",  "id": "13320123", "duration": 6.0, "desc": "Medusa bioluminiscente glowing"},
        {"seg": "11-17", "id": "16521053", "duration": 6.0, "desc": "Medusa flotando ciclo vital"},
        {"seg": "17-23", "id": "12210147", "duration": 6.0, "desc": "Criatura marina profunda — biologia"},
        {"seg": "23-29", "id": "8950635",  "duration": 6.0, "desc": "Medusa glowing — investigacion"},
        {"seg": "29-32", "id": "2840467",  "duration": 3.0, "desc": "Medusa cierre — CTA"},
    ],

    # Overlays ajustados a duracion real del voiceover (29.45s)
    "overlays": [
        {
            "text": "Este animal NO puede MORIR",
            "fontsize": 78, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 200, "t_start": 0, "t_end": 5,
        },
        {
            "text": "Inmortalidad biologica REAL",
            "fontsize": 62, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": "h/3", "t_start": 11, "t_end": 19,
        },
        {
            "text": "Sigueme para mas datos increibles",
            "fontsize": 56, "color": "white", "bordercolor": "black", "borderw": 4,
            "y": "h/2+100", "t_start": 25, "t_end": 29,
        },
    ],

    "thumbnail_texts": [
        {"text": "Este animal NO puede MORIR", "fontsize": 86, "color": "white", "y": 250},
        {"text": "Turritopsis dohrnii", "fontsize": 52, "color": "yellow", "y": 380},
    ],

    "subtitle_fontsize": 58,
}
