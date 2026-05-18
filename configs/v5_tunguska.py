"""
Config V5 — "Algo destruyo 2,000 km2 de bosque y nadie sabe que fue" (Evento Tunguska 1908)
Sub-nicho: Misterio sin resolver | V-Score: 8.9 | Duracion real voiceover: 68s
Horario: Lunes 2026-05-18 20:00 CDMX
Guion: G04 sprint2_guiones_outlier.md
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_03_2026-05-18_a_2026-05-24"

VIDEO_CONFIG = {
    "video_id": "V5",
    "voiceover": "V5_Tunguska.mp3",
    "output_dir": str(SEMANA / "LUNES" / "OUTPUT"),

    "caption_tiktok": (
        "El 30 de junio de 1908 algo destruyo 2,000 km2 de bosque en Siberia. "
        "1,000 veces mas potente que Hiroshima. Sin crater. Sin meteorito. 113 anos sin explicacion oficial. "
        "Y en 2013 paso de nuevo. #misterio #tunguska #sinresolver #ciencia #curioclip "
        "#datoscuriosos #sabiasque #rusia #siberia #espacio"
    ),

    # B-roll TEMATICO de Pexels — bosques, cometas, expediciones cientificas
    # IDs verificados via broll_finder
    # IDs verificados via broll_finder.py — Pexels real | total 68s (cubre voiceover)
    "broll_plan": [
        {"seg": "0-6",   "id": "11071481", "duration": 6.0, "desc": "Bosque siberiano aereo — hook"},
        {"seg": "6-12",  "id": "35682974", "duration": 6.0, "desc": "Explosion cielo nocturno"},
        {"seg": "12-18", "id": "5764717",  "duration": 6.0, "desc": "Arboles caidos patron"},
        {"seg": "18-24", "id": "856309",   "duration": 6.0, "desc": "Cometa meteoro espacio"},
        {"seg": "24-30", "id": "27797620", "duration": 6.0, "desc": "Bosque pino denso"},
        {"seg": "30-36", "id": "8678510",  "duration": 6.0, "desc": "Wilderness rusia"},
        {"seg": "36-42", "id": "11071481", "duration": 6.0, "desc": "Bosque siberiano loop"},
        {"seg": "42-48", "id": "856309",   "duration": 6.0, "desc": "Cometa teoria oficial"},
        {"seg": "48-54", "id": "5764717",  "duration": 6.0, "desc": "Arboles caidos loop"},
        {"seg": "54-60", "id": "35682974", "duration": 6.0, "desc": "Explosion cielo loop"},
        {"seg": "60-68", "id": "8678510",  "duration": 8.0, "desc": "Chelyabinsk 2013 cierre CTA"},
    ],

    "overlays": [
        {
            "text": "1908: bosque DESTRUIDO",
            "fontsize": 78, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 200, "t_start": 0, "t_end": 6,
        },
        {
            "text": "Sin crater. Sin meteorito.",
            "fontsize": 64, "color": "red", "bordercolor": "black", "borderw": 4,
            "y": 280, "t_start": 10, "t_end": 17,
        },
        {
            "text": "1,000x mas que Hiroshima",
            "fontsize": 68, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": "h/3", "t_start": 22, "t_end": 30,
        },
        {
            "text": "113 anos SIN explicacion",
            "fontsize": 66, "color": "cyan", "bordercolor": "black", "borderw": 4,
            "y": "h/2", "t_start": 50, "t_end": 58,
        },
        {
            "text": "2013: paso de nuevo",
            "fontsize": 70, "color": "red", "bordercolor": "black", "borderw": 5,
            "y": 320, "t_start": 60, "t_end": 68,
        },
    ],

    "thumbnail_texts": [
        {"text": "DESTRUIDOS", "fontsize": 110, "color": "red", "y": 280},
        {"text": "2,000 km2 de bosque", "fontsize": 64, "color": "white", "y": 420},
        {"text": "Nadie sabe que fue", "fontsize": 56, "color": "yellow", "y": 520},
    ],

    "subtitle_fontsize": 56,
}
