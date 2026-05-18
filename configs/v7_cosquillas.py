"""
Config V7 — "Intenta hacerte cosquillas a ti mismo" (Prediccion sensorial)
Sub-nicho: Psicologia interactivo | V-Score: 8.1 | Duracion real voiceover: 39s
Horario: Lunes 2026-05-18 23:30 CDMX
Guion: G15 sprint2_guiones_outlier.md
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_03_2026-05-18_a_2026-05-24"

VIDEO_CONFIG = {
    "video_id": "V7",
    "voiceover": "V7_Cosquillas.mp3",
    "output_dir": str(SEMANA / "MIERCOLES" / "OUTPUT"),

    "caption_tiktok": (
        "Intenta hacerte cosquillas a ti mismo ahora. No funciona. Y la razon es ESTA: "
        "tu cerebro predice exactamente lo que vas a sentir antes de sentirlo. "
        "Pero hay un truco con delay de 200ms que SI funciona. "
        "#psicologia #cerebro #cosquillas #neurociencia #curioclip #datoscuriosos "
        "#sabiasque #experimento #cienciawtf"
    ),

    # IDs verificados via broll_finder.py — Pexels real | total 40s
    "broll_plan": [
        {"seg": "0-5",   "id": "8724231",  "duration": 5.0, "desc": "Persona sonriendo cara — hook"},
        {"seg": "5-10",  "id": "18388881", "duration": 5.0, "desc": "Cerebro neuronas animacion"},
        {"seg": "10-15", "id": "3752451",  "duration": 5.0, "desc": "Mano pluma piel — sensacion"},
        {"seg": "15-20", "id": "5724101",  "duration": 5.0, "desc": "Cerebro escaneo neurologia"},
        {"seg": "20-25", "id": "18388881", "duration": 5.0, "desc": "Neuronas prediccion loop"},
        {"seg": "25-30", "id": "8724231",  "duration": 5.0, "desc": "Risa loop cosquillas"},
        {"seg": "30-35", "id": "6153727",  "duration": 5.0, "desc": "Robot mano tecnologia"},
        {"seg": "35-40", "id": "3752451",  "duration": 5.0, "desc": "Pluma cierre CTA"},
    ],

    "overlays": [
        {
            "text": "Hazte cosquillas. AHORA.",
            "fontsize": 76, "color": "yellow", "bordercolor": "black", "borderw": 5,
            "y": 200, "t_start": 0, "t_end": 5,
        },
        {
            "text": "No funciona. NUNCA.",
            "fontsize": 72, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 280, "t_start": 6, "t_end": 12,
        },
        {
            "text": "Tu cerebro lo PREDICE",
            "fontsize": 66, "color": "cyan", "bordercolor": "black", "borderw": 4,
            "y": "h/3", "t_start": 14, "t_end": 22,
        },
        {
            "text": "Robot 200ms = SI funciona",
            "fontsize": 64, "color": "red", "bordercolor": "black", "borderw": 4,
            "y": "h/2", "t_start": 30, "t_end": 39,
        },
    ],

    "thumbnail_texts": [
        {"text": "Hazte cosquillas", "fontsize": 80, "color": "yellow", "y": 250},
        {"text": "NO FUNCIONA", "fontsize": 110, "color": "red", "y": 360},
        {"text": "La ciencia lo explica", "fontsize": 50, "color": "white", "y": 500},
    ],

    "subtitle_fontsize": 56,
    "duration_s": 40.0,
}
