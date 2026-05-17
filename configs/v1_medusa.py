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

    # B-roll CC0 — solo IDs verificados como videos reales (>10MB, duracion confirmada)
    # 5377700=microscopia celular 26s | 3571264=laboratorio 33s | 3129671=cosmos 40s
    # IDs 4666749/4666752/6981032 eran fotos Pexels, no videos — REEMPLAZADOS
    "broll_plan": [
        {"seg": "0-5",   "id": "5377700",  "duration": 5.0, "desc": "Microscopia celular — vida invisible (hook biologia)"},
        {"seg": "5-11",  "id": "3571264",  "duration": 6.0, "desc": "Laboratorio cientifico — investigacion ADN"},
        {"seg": "11-17", "id": "3129671",  "duration": 6.0, "desc": "Cosmos — escala del tiempo inmortal"},
        {"seg": "17-23", "id": "3571264",  "duration": 6.0, "desc": "Laboratorio — estudio Turritopsis"},
        {"seg": "23-29", "id": "3129671",  "duration": 6.0, "desc": "Universo — reflexion vida eterna"},
        {"seg": "29-32", "id": "5377700",  "duration": 3.0, "desc": "Celulas — cierre biologico CTA"},
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
