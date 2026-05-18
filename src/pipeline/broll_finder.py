"""
B-Roll Finder — Pexels API thematic video discovery
=====================================================
Busca y verifica videos de Pexels por tematica/query. Filtra:
  - Es video real (no foto) con duracion >= 10s
  - Resolucion >= 720p en el archivo HD/SD principal
  - Aspect ratio compatible con vertical 9:16 (despues se hace crop)

Uso CLI:
    python -m src.pipeline.broll_finder --query "jellyfish ocean" --count 5
    python -m src.pipeline.broll_finder --build-library V1 V3 V4

Uso programatico:
    from src.pipeline.broll_finder import search_pexels_videos
    ids = search_pexels_videos("jellyfish", min_count=5)
"""
import os, sys, json, time
sys.stdout.reconfigure(encoding="utf-8")
import urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
LIBRARY_PATH = ROOT / "obsidian_vault" / "30_Contenido" / "broll_library.json"

# Cargar .env
_env = ROOT / ".env"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v.strip().strip('"').strip("'"))

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
if not PEXELS_API_KEY:
    print("[WARN] PEXELS_API_KEY no configurada en .env")


# ─── Queries tematicas por video ───────────────────────────────────────────

THEMATIC_QUERIES = {
    "V1": {  # Medusa inmortal
        "topic": "Turritopsis dohrnii — animal biologicamente inmortal",
        "queries": ["jellyfish ocean", "jellyfish glowing", "deep sea creature",
                    "bioluminescence underwater", "marine biology lab", "DNA research"],
        "min_videos": 6,
    },
    "V2": {  # Bacterias galaxia
        "topic": "Bacterias del cuerpo vs estrellas Via Lactea",
        "queries": ["milky way galaxy", "bacteria microscope", "human cells",
                    "cosmos space", "microbiology lab", "human body anatomy"],
        "min_videos": 6,
    },
    "V3": {  # Radio UVB-76
        "topic": "UVB-76 senal misteriosa rusa desde 1973",
        "queries": ["radio antenna tower", "old soviet building", "abandoned facility",
                    "night city dark", "radio equipment vintage", "mysterious lights"],
        "min_videos": 6,
    },
    "V4": {  # Leyes absurdas USA
        "topic": "Leyes raras de Estados Unidos",
        "queries": ["american flag patriotic", "courthouse justice", "law books",
                    "small town america", "judge gavel", "USA city street"],
        "min_videos": 6,
    },
    "V5": {  # Tunguska 1908 — misterio sin resolver
        "topic": "Evento Tunguska 1908 — explosion sin explicacion",
        "queries": ["siberian forest aerial", "explosion night sky", "dense pine forest",
                    "comet meteor space", "fallen trees forest", "remote wilderness russia"],
        "min_videos": 6,
    },
    "V6": {  # Conan bacterium — resistencia nuclear
        "topic": "Deinococcus radiodurans — bacteria que sobrevive a bombas nucleares",
        "queries": ["nuclear explosion mushroom", "petri dish bacteria", "dna helix animation",
                    "scientist microscope lab", "radiation symbol", "microbiology research"],
        "min_videos": 5,
    },
    "V7": {  # Cosquillas — neurociencia interactivo
        "topic": "Por que no puedes hacerte cosquillas — prediccion sensorial",
        "queries": ["person laughing close up", "brain neurons animation", "feather skin macro",
                    "brain scan medical", "robot hand technology", "neuroscience brain mri"],
        "min_videos": 5,
    },
}


# ─── Pexels API ────────────────────────────────────────────────────────────

def pexels_search(query: str, per_page: int = 15, orientation: str = "") -> list[dict]:
    """Busca videos en Pexels. Retorna lista de dicts con id, duration, url, video_files."""
    params = {
        "query": query,
        "per_page": per_page,
        "size": "medium",  # 720p+
    }
    if orientation:
        params["orientation"] = orientation
    url = f"https://api.pexels.com/videos/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "CurioClip-Bot/1.0 (Marketing Agency Pipeline)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        return data.get("videos", [])
    except Exception as e:
        print(f"[ERROR] Pexels search '{query}': {e}")
        return []


def is_valid_video(v: dict, min_duration: int = 10) -> bool:
    """Filtra videos: duracion suficiente, archivos HD/SD legitimos."""
    if v.get("duration", 0) < min_duration:
        return False
    files = v.get("video_files", [])
    if not files:
        return False
    # Verificar que haya al menos un archivo de calidad razonable
    has_quality = any(
        (f.get("width", 0) >= 720 or f.get("height", 0) >= 720) and
        f.get("file_type", "").startswith("video/")
        for f in files
    )
    return has_quality


def best_video_url(v: dict, target_height: int = 1920) -> str | None:
    """Selecciona el mejor archivo del video — prefiere vertical >= 1080p."""
    files = v.get("video_files", [])
    if not files:
        return None
    # Ordenar por height descendente, preferir vertical
    files_sorted = sorted(
        files,
        key=lambda f: (
            1 if f.get("height", 0) >= f.get("width", 0) else 0,  # vertical first
            f.get("height", 0),
        ),
        reverse=True,
    )
    return files_sorted[0].get("link")


# ─── Discovery & verification ──────────────────────────────────────────────

def search_pexels_videos(query: str, min_count: int = 5,
                          min_duration: int = 10) -> list[dict]:
    """Busca y filtra. Retorna lista de videos validos con metadatos."""
    print(f"  [PEXELS] query='{query}'...", end=" ")
    raw = pexels_search(query, per_page=20)
    valid = [v for v in raw if is_valid_video(v, min_duration)]
    print(f"raw={len(raw)} valid={len(valid)}")
    results = []
    for v in valid[:min_count]:
        results.append({
            "id": str(v["id"]),
            "duration": v.get("duration", 0),
            "url": v.get("url", ""),
            "download_url": best_video_url(v),
            "width": v.get("width", 0),
            "height": v.get("height", 0),
            "query": query,
        })
    return results


def build_library_for_video(video_id: str) -> dict:
    """Construye biblioteca de b-roll para un video especifico (V1, V2, V3, V4)."""
    if video_id not in THEMATIC_QUERIES:
        return {"error": f"Unknown video_id: {video_id}"}
    cfg = THEMATIC_QUERIES[video_id]
    print(f"\n{'='*60}")
    print(f"BUILDING LIBRARY: {video_id} — {cfg['topic']}")
    print(f"{'='*60}")
    all_videos = []
    seen_ids = set()
    for q in cfg["queries"]:
        for v in search_pexels_videos(q, min_count=3):
            if v["id"] not in seen_ids:
                seen_ids.add(v["id"])
                all_videos.append(v)
        time.sleep(0.5)  # rate limit cortesia
    print(f"  TOTAL VALID: {len(all_videos)} videos unicos")
    return {
        "video_id": video_id,
        "topic": cfg["topic"],
        "queries_used": cfg["queries"],
        "videos": all_videos,
    }


def build_full_library(video_ids: list[str]) -> dict:
    """Construye biblioteca para multiples videos y guarda en JSON."""
    library = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "videos": {}}
    for vid in video_ids:
        library["videos"][vid] = build_library_for_video(vid)
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LIBRARY_PATH.write_text(json.dumps(library, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] Library saved to: {LIBRARY_PATH}")
    return library


# ─── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Uso:")
        print("  python -m src.pipeline.broll_finder --query <q> [--count N]")
        print("  python -m src.pipeline.broll_finder --build-library V1 V3 V4")
        sys.exit(0)
    if "--build-library" in args:
        idx = args.index("--build-library")
        video_ids = [v for v in args[idx+1:] if v in THEMATIC_QUERIES]
        if not video_ids:
            video_ids = list(THEMATIC_QUERIES.keys())
        build_full_library(video_ids)
    elif "--query" in args:
        idx = args.index("--query")
        query = args[idx+1]
        count = 5
        if "--count" in args:
            count = int(args[args.index("--count")+1])
        results = search_pexels_videos(query, min_count=count)
        print(json.dumps(results, ensure_ascii=False, indent=2))
