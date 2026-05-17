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

    # B-roll TEMATICO de Pexels — antenas radio, edificios sovieticos, lugares misteriosos
    # 37525184=radio antenna tower 31s | 10354219=radio antenna 54s | 12959226=antena 75s
    # 18584563=soviet building 20s vertical | 10095265=abandoned facility 25s
    # 37410541=night city dark 25s | 13188717=soviet building 17s
    # Voiceover V3=41.09s → broll total 44s (buffer 3s con -shortest)
    "broll_plan": [
        {"seg": "0-6",   "id": "37525184", "duration": 6.0, "desc": "Antena radio torre — hook UVB-76"},
        {"seg": "6-12",  "id": "18584563", "duration": 6.0, "desc": "Edificio sovietico abandonado — 1973"},
        {"seg": "12-18", "id": "10354219", "duration": 6.0, "desc": "Antena transmision — la senal"},
        {"seg": "18-24", "id": "10095265", "duration": 6.0, "desc": "Facility abandonada — el misterio"},
        {"seg": "24-30", "id": "12959226", "duration": 6.0, "desc": "Antena noche — CIA no puede explicar"},
        {"seg": "30-36", "id": "37410541", "duration": 6.0, "desc": "Ciudad oscura — 50 anos"},
        {"seg": "36-42", "id": "13188717", "duration": 6.0, "desc": "Edificio sovietico — cierre"},
        {"seg": "42-44", "id": "18584563", "duration": 2.0, "desc": "Buffer — CTA comenta que crees"},
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
