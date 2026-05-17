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

    # B-roll CC0 extendido a 38s — IDs: medusa (con setsar=1 para JPEGs), laboratorio
    "broll_plan": [
        {"seg": "0-4",   "id": "4666749",  "duration": 4.0, "desc": "Medusa glowing — hook impacto"},
        {"seg": "4-9",   "id": "6981032",  "duration": 5.0, "desc": "Medusa ciclo de vida"},
        {"seg": "9-14",  "id": "4666752",  "duration": 5.0, "desc": "Comparacion viejo a joven"},
        {"seg": "14-20", "id": "3571264",  "duration": 6.0, "desc": "Laboratorio cientifico — dato"},
        {"seg": "20-25", "id": "4666749",  "duration": 5.0, "desc": "Medusa flotando"},
        {"seg": "25-30", "id": "6981032",  "duration": 5.0, "desc": "Ciclo vital invertido"},
        {"seg": "30-35", "id": "3571264",  "duration": 5.0, "desc": "Investigacion cientifica"},
        {"seg": "35-38", "id": "4666752",  "duration": 3.0, "desc": "Cierre + CTA"},
    ],

    # Overlays de texto (hook 0-3s + CTA 17-22s)
    "overlays": [
        {
            "text": "Este animal NO puede MORIR",
            "fontsize": 78, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 200, "t_start": 0, "t_end": 3,
        },
        {
            "text": "Sigues para mas datos increibles",
            "fontsize": 56, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": "h/2+80", "t_start": 17, "t_end": 22,
        },
    ],

    "thumbnail_texts": [
        {"text": "Este animal NO puede MORIR", "fontsize": 86, "color": "white", "y": 250},
        {"text": "Turritopsis dohrnii", "fontsize": 52, "color": "yellow", "y": 380},
    ],

    "subtitle_fontsize": 50,
}
