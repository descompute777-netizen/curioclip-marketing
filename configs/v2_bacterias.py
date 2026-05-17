"""
Config V2 — "Tu cuerpo tiene más bacterias que estrellas en la galaxia"
Sub-nicho: Comparación imposible | Hook score: 9/10 | Duración: 45s
Horario: Lunes 12:00 CDMX
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_02_2026-05-13_a_2026-05-19"

VIDEO_CONFIG = {
    "video_id": "V2",
    "voiceover": "V2_Bacterias.mp3",
    "output_dir": str(SEMANA / "LUNES" / "OUTPUT"),

    # Caption para TikTok (incluye hashtags)
    "caption_tiktok": (
        "Sabias que tu cuerpo tiene MAS bacterias que estrellas en la Via Lactea? "
        "38 billones de bacterias te hacen quien eres. Tu microbioma te supera por mucho. "
        "#curiosidades #datoscuriosos #sabiasque #ciencia #bacteria #galaxia #cuerpohumano "
        "#biologia #mente #CurioClip #viral #aprender"
    ),

    # B-roll CC0 extendido a 45s — loopea segmentos para cubrir el voiceover completo
    "broll_plan": [
        {"seg": "0-4",   "id": "3129671",  "duration": 4.0, "desc": "Via Lactea — hook visual impactante"},
        {"seg": "4-8",   "id": "5377700",  "duration": 4.0, "desc": "Bacteria microscopio animacion"},
        {"seg": "8-13",  "id": "3214460",  "duration": 5.0, "desc": "Cuerpo humano celulas"},
        {"seg": "13-18", "id": "3129671",  "duration": 5.0, "desc": "Galaxia zoom dramatico"},
        {"seg": "18-22", "id": "5377700",  "duration": 4.0, "desc": "Bacteria comparacion"},
        {"seg": "22-27", "id": "3571264",  "duration": 5.0, "desc": "Laboratorio cientifico — dato"},
        {"seg": "27-31", "id": "3214460",  "duration": 4.0, "desc": "Cuerpo humano interior"},
        {"seg": "31-36", "id": "3129671",  "duration": 5.0, "desc": "Cosmos expansion — impacto"},
        {"seg": "36-40", "id": "5377700",  "duration": 4.0, "desc": "Bacteria final — reflexion"},
        {"seg": "40-45", "id": "3571264",  "duration": 5.0, "desc": "Cierre cientifico — CTA"},
    ],

    "overlays": [
        {
            "text": "Tu cuerpo vs la GALAXIA",
            "fontsize": 82, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 180, "t_start": 0, "t_end": 4,
        },
        {
            "text": "38 BILLONES de bacterias",
            "fontsize": 72, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": 300, "t_start": 4, "t_end": 10,
        },
        {
            "text": "MAS que estrellas en la Via Lactea",
            "fontsize": 58, "color": "cyan", "bordercolor": "black", "borderw": 4,
            "y": "h/3", "t_start": 13, "t_end": 20,
        },
        {
            "text": "Sigues para mas datos increibles",
            "fontsize": 62, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": "h/2+80", "t_start": 38, "t_end": 45,
        },
    ],

    "thumbnail_texts": [
        {"text": "Tu cuerpo vs", "fontsize": 72, "color": "white", "y": 220},
        {"text": "la GALAXIA", "fontsize": 110, "color": "yellow", "y": 320},
        {"text": "38 BILLONES de bacterias", "fontsize": 52, "color": "red", "y": 460},
    ],

    "subtitle_fontsize": 52,
}
