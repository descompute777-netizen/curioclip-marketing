"""
Config V6 — "La bacteria que sobrevive a una bomba nuclear" (Deinococcus radiodurans)
Sub-nicho: Biologia WTF | V-Score: 8.2 | Duracion real voiceover: 59s
Horario: Lunes 2026-05-18 22:00 CDMX
Guion: G09 sprint2_guiones_outlier.md
"""
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_03_2026-05-18_a_2026-05-24"

VIDEO_CONFIG = {
    "video_id": "V6",
    "voiceover": "V6_Conan.mp3",
    "output_dir": str(SEMANA / "MARTES" / "OUTPUT"),

    "caption_tiktok": (
        "Existe una bacteria que sobrevive a una bomba nuclear. La apodaron Conan The Bacterium. "
        "Resiste 3,000 veces mas radiacion que un humano. Reconstruye su ADN destrozado en horas. "
        "Y podria curarnos del cancer y la radiacion. #ciencia #bacteria #nuclear #biologia "
        "#curioclip #datoscuriosos #sabiasque #cienciawtf"
    ),

    # IDs verificados via broll_finder.py — Pexels real | total 59s
    "broll_plan": [
        {"seg": "0-6",   "id": "30716160", "duration": 6.0, "desc": "Hongo nuclear explosion — hook"},
        {"seg": "6-12",  "id": "31767895", "duration": 6.0, "desc": "Bacteria microscopio petri"},
        {"seg": "12-18", "id": "31801592", "duration": 6.0, "desc": "ADN helix"},
        {"seg": "18-24", "id": "32402606", "duration": 6.0, "desc": "Cientifico microscopio lab"},
        {"seg": "24-30", "id": "8540170",  "duration": 6.0, "desc": "Investigacion microbiologia"},
        {"seg": "30-36", "id": "31767895", "duration": 6.0, "desc": "Bacteria petri loop"},
        {"seg": "36-42", "id": "30716160", "duration": 6.0, "desc": "Hongo nuclear loop"},
        {"seg": "42-48", "id": "31801592", "duration": 6.0, "desc": "ADN reparacion loop"},
        {"seg": "48-54", "id": "32402606", "duration": 6.0, "desc": "Lab cientifico loop"},
        {"seg": "54-60", "id": "8540170",  "duration": 6.0, "desc": "Microbiologia cierre"},
    ],

    "overlays": [
        {
            "text": "Bacteria vs BOMBA NUCLEAR",
            "fontsize": 74, "color": "white", "bordercolor": "black", "borderw": 5,
            "y": 200, "t_start": 0, "t_end": 6,
        },
        {
            "text": "3,000 VECES mas resistente",
            "fontsize": 66, "color": "yellow", "bordercolor": "black", "borderw": 4,
            "y": 280, "t_start": 8, "t_end": 16,
        },
        {
            "text": "Reconstruye su ADN en HORAS",
            "fontsize": 58, "color": "cyan", "bordercolor": "black", "borderw": 4,
            "y": "h/3", "t_start": 18, "t_end": 26,
        },
        {
            "text": "1956: la sobrevivio",
            "fontsize": 62, "color": "white", "bordercolor": "black", "borderw": 4,
            "y": 280, "t_start": 30, "t_end": 38,
        },
        {
            "text": "Podria curar el CANCER",
            "fontsize": 68, "color": "red", "bordercolor": "black", "borderw": 5,
            "y": "h/2", "t_start": 44, "t_end": 56,
        },
    ],

    "thumbnail_texts": [
        {"text": "Sobrevive a una", "fontsize": 70, "color": "white", "y": 240},
        {"text": "BOMBA NUCLEAR", "fontsize": 100, "color": "red", "y": 340},
        {"text": "Una sola bacteria", "fontsize": 56, "color": "yellow", "y": 480},
    ],

    "subtitle_fontsize": 56,
}
