"""
produce_pipeline.py — Generador de video CANÓNICO de CurioClip (v2, 2026-05-29)
================================================================================
Reemplaza a produce_week_remaining.py, que generaba videos inviralizables:
b-roll 75% reciclado, elegido por NICHO genérico (Venus→Tierra), SIN subtítulos.

Este pipeline cablea correctamente las piezas que ya existían + añade los gates
que faltaban. Cada video pasa por 6 etapas con checkpoints (R10-R16 del CLAUDE.md):

  1. COMPLIANCE GATE (A9)  — rechaza reposts de terceros ("creditos:@", IP ajena).
  2. HOOK GATE (R16)        — exige hook auto-referencial (plantillas A/B/C/D).
  3. TTS (R12)              — voz única por video vía voice_pool (edge-tts).
  4. B-ROLL POR ESCENA      — query semántica por línea del guion + DEDUP GLOBAL
                              (R10: cero reciclaje, b-roll temático real).
  5. COMPOSE + SUBTÍTULOS   — subtítulos hardcoded whisper estilo TikTok (R11).
  6. QUALITY GATE (R13)     — verifica subs, dedup, duración, resolución, audio.
                              Si UNO falla → el video NO se marca listo.

CONTRATO DE ENTRADA (script dict / JSON):
{
  "id": "V21",
  "niche": "cosmologia",
  "hook": "¿Qué pasaría si pudieras sostener un trozo de estrella?",
  "voiceover_text": "<narración completa, incluye el hook hablado>",
  "scenes": [                          # opcional pero RECOMENDADO (lo da el LLM)
     {"text": "...", "broll_query": "neutron star space"},   # query EN INGLÉS
     {"text": "...", "broll_query": "collapsing star animation"}
  ],
  "caption": "...",
  "hashtags": ["#espacio", "#ciencia"]
}
Si faltan `scenes`, se autosegmenta el voiceover en frases y se deriva una query
con un extractor de keywords ES→EN básico (best-effort; el LLM debe dar scenes).

Uso CLI:
  python scripts/autonomous/produce_pipeline.py --demo
  python scripts/autonomous/produce_pipeline.py --script guion.json --out output/V21
"""
from __future__ import annotations
import os, sys, re, json, math, time, subprocess, urllib.request
from pathlib import Path
from dataclasses import dataclass, field, asdict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Reusar infraestructura existente (las piezas que SÍ funcionan) ──────────────
from scripts.autonomous.generate_voiceover import generate_voiceover
from scripts.autonomous.generate_subs_ass import (
    transcribe_with_timestamps, group_chunks, build_ass,
)
from src.pipeline.broll_finder import search_pexels_videos, best_video_url

# Ledger GLOBAL de b-roll usado (dedup que abarca TODA la historia de la cuenta)
BROLL_LEDGER = ROOT / "obsidian_vault" / "30_Contenido" / "broll_used.json"
W, H, FPS = 1080, 1920, 30


# ─── TTS: ElevenLabs (cálida/humana, voz ROTATIVA) con fallback a edge-tts ─────
def _synthesize_voice(text: str, out: Path, vid: str, voice_id: str | None = None) -> str:
    """ElevenLabs con voz rotativa por video (R12). Devuelve el nombre de la voz usada.
    Prioridad: voice_id explícito (lote) > pool rotativo por guion_id > edge-tts."""
    provider = os.environ.get("TTS_PROVIDER", "").lower()
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if provider == "elevenlabs" and key and not key.startswith("<<<"):
        try:
            from scripts.autonomous.tts_elevenlabs import synth, pick_voice
            if voice_id:
                vname = next((n for n, i in __import__("scripts.autonomous.tts_elevenlabs",
                             fromlist=["VOICE_POOL"]).VOICE_POOL if i == voice_id), "custom")
            else:
                vname, voice_id = pick_voice(vid)
            print(f"[TTS] ElevenLabs voz={vname} ({voice_id})")
            synth(text, out, voice_id)
            return vname
        except Exception as e:
            print(f"[TTS] ElevenLabs falló ({str(e)[:120]}) → fallback edge-tts")
    generate_voiceover(text, out, guion_id=vid, account="fugamental28")
    return "edge-tts"


# ═══════════════════════════════════════════════════════════════════════════
# 1. COMPLIANCE GATE (A9) — la causa #1 de las restricciones de @fugamental28
# ═══════════════════════════════════════════════════════════════════════════
# Patrones que delatan repost de contenido ajeno (uso no autorizado → strike).
_REPOST_SIGNALS = [
    r"cr[ée]ditos?\s*[:@]", r"cr[ée]dito\s+a\b", r"\bvia\s*@", r"\brepost",
    r"no\s+me\s+pertenece", r"todos?\s+los\s+derechos?\s+a", r"©", r"\bDR\b",
    r"sigue\s+a\s*@", r"@[A-Za-z0-9._]{3,}",   # mención a otra cuenta en caption
]

class ComplianceError(Exception):
    pass

def compliance_gate(script: dict) -> None:
    """A9 con poder de VETO (R1/R2). Rechaza cualquier señal de repost ajeno."""
    blob = " ".join(str(script.get(k, "")) for k in ("caption", "voiceover_text", "hook"))
    blob += " " + " ".join(script.get("hashtags", []))
    for pat in _REPOST_SIGNALS:
        m = re.search(pat, blob, re.IGNORECASE)
        if m:
            raise ComplianceError(
                f"VETO A9: señal de contenido de terceros detectada → '{m.group(0)}'. "
                f"Dar créditos NO sustituye una licencia (R2). Solo se publica contenido "
                f"100% original: b-roll stock licenciado + voz propia + edición propia."
            )
    # b-roll debe venir de stock licenciado (Pexels). Esto se garantiza por diseño:
    # el pipeline SOLO descarga de la API de Pexels (licencia libre, sin atribución).


# ═══════════════════════════════════════════════════════════════════════════
# 2. HOOK GATE (R16) — hook auto-referencial / condicional hipotético
# ═══════════════════════════════════════════════════════════════════════════
_HOOK_OK = [
    r"^\s*¿?\s*qu[ée]\s+pasar[íi]a\s+si",          # A
    r"^\s*(prueba|mira|haz|intenta|p[áa]rate|cierra|toca|imagina que t[úu])",  # B
    r"^\s*¿?\s*por\s+qu[ée]\s+cuando\s+(t[úu]|tu)",  # C
    r"^\s*¿?\s*alguna\s+vez",                       # auto-referencial
    r"^\s*si\s+(tú|tu|alguna vez)",
]
_HOOK_BAN = [
    r"^\s*¿?\s*sab[íi]as\s+que",                    # sobreusado
    r"^\s*¿?\s*te\s+imaginas\s+que",                # sobreusado
    r"^\s*existe\s+",                               # no involucra
    r"^\s*el\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}",     # fecha + sujeto histórico
]

class HookError(Exception):
    pass

def hook_gate(hook: str) -> None:
    h = (hook or "").strip()
    if not h:
        raise HookError("R8/R16: hook vacío. El guion está incompleto.")
    for pat in _HOOK_BAN:
        if re.search(pat, h, re.IGNORECASE):
            raise HookError(f"R16: hook prohibido (patrón '{pat}'). Usar plantilla A/B/C/D.")
    if not any(re.search(p, h, re.IGNORECASE) for p in _HOOK_OK):
        raise HookError(
            f"R16: el hook no es auto-referencial → '{h[:60]}'. Debe empezar con "
            f"'¿Qué pasaría si...', 'Prueba esto...', '¿Por qué cuando tú...', etc."
        )


# ═══════════════════════════════════════════════════════════════════════════
# 4. B-ROLL POR ESCENA con DEDUP GLOBAL (R10)
# ═══════════════════════════════════════════════════════════════════════════
# Mapa ES→EN mínimo para fallback cuando el guion no trae scenes con query EN.
_ES_EN = {
    "cerebro": "brain neurons", "espacio": "outer space", "estrella": "star space",
    "agujero negro": "black hole", "oceano": "deep ocean", "océano": "deep ocean",
    "mar": "ocean waves", "cuerpo": "human body anatomy", "celula": "cells microscope",
    "célula": "cells microscope", "bacteria": "bacteria microscope", "adn": "dna helix",
    "planeta": "planet space", "sol": "sun solar", "luna": "moon surface",
    "agua": "water flowing", "fuego": "fire flames", "ciudad": "city aerial night",
    "tiempo": "clock time lapse", "dinero": "money cash", "corazon": "human heart beating",
    "corazón": "human heart beating", "ojo": "human eye macro", "musica": "music waves",
    "música": "music waves", "memoria": "brain memory", "sueño": "sleeping person night",
    "miedo": "dark scary corridor", "animal": "wildlife animal", "volcan": "volcano eruption",
    "volcán": "volcano eruption", "hielo": "ice glacier", "desierto": "desert sand dunes",
    "selva": "jungle rainforest", "robot": "robot technology", "computadora": "computer code",
}
_STOP = set("el la los las un una unos unas de del a en y o que se su tu por con para es son "
            "como más pero si no lo le les al un una era fue han hay este esta esto muy".split())

def _derive_query(text: str, niche: str) -> str:
    """Fallback: extrae el sustantivo más relevante de la frase ES → query EN."""
    low = text.lower()
    for es, en in _ES_EN.items():
        if es in low:
            return en
    words = [w for w in re.findall(r"[a-záéíóúñ]{4,}", low) if w not in _STOP]
    base = words[0] if words else niche
    return f"{base} cinematic"  # Pexels tolera algo de ES; último recurso

def _load_ledger() -> set:
    if BROLL_LEDGER.exists():
        try:
            return set(json.loads(BROLL_LEDGER.read_text(encoding="utf-8")).get("used_ids", []))
        except Exception:
            return set()
    return set()

def _save_ledger(used: set) -> None:
    BROLL_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    BROLL_LEDGER.write_text(json.dumps({"used_ids": sorted(used),
                            "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ")},
                            ensure_ascii=False, indent=2), encoding="utf-8")

def _download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CurioClip-Bot/2.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
        return dest.stat().st_size > 50_000
    except Exception as e:
        print(f"    [DL ERROR] {e}")
        return False

def fetch_scene_broll(scenes: list[dict], niche: str, out_dir: Path,
                      used_ids: set) -> list[Path]:
    """Un clip ÚNICO y temático por escena. Nunca reutiliza un id ya usado (global)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    for i, sc in enumerate(scenes):
        query = (sc.get("broll_query") or _derive_query(sc.get("text", ""), niche)).strip()
        candidates = search_pexels_videos(query, min_count=12, min_duration=4)
        # ampliar búsqueda si todo ya fue usado
        if all(c["id"] in used_ids for c in candidates):
            candidates += search_pexels_videos(f"{query} 4k", min_count=12, min_duration=4)
        picked = next((c for c in candidates if c["id"] not in used_ids), None)
        if not picked:
            print(f"    [BROLL] escena {i}: SIN clip único para '{query}' → gate fallará")
            continue
        dest = out_dir / f"scene_{i:02d}_{picked['id']}.mp4"
        url = picked.get("download_url") or best_video_url(picked)
        if url and _download(url, dest):
            used_ids.add(picked["id"])
            clips.append(dest)
            print(f"    [BROLL] escena {i}: '{query}' → id={picked['id']} ✓")
        time.sleep(0.4)  # cortesía rate-limit
    return clips


# ═══════════════════════════════════════════════════════════════════════════
# 5. COMPOSE + SUBTÍTULOS HARDCODED (R11)
# ═══════════════════════════════════════════════════════════════════════════
def _ffprobe_dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except Exception:
        return 0.0

def _scene_durations(scenes: list[dict], total: float, n_clips: int) -> list[float]:
    """Reparte la duración total proporcional al largo del texto de cada escena."""
    lens = [max(len(s.get("text", "")), 1) for s in scenes[:n_clips]]
    tot = sum(lens) or 1
    durs = [max(total * l / tot, 2.0) for l in lens]
    # normalizar para que sumen exactamente `total`
    k = total / sum(durs)
    durs = [round(d * k, 3) for d in durs]
    durs[-1] = round(total - sum(durs[:-1]), 3)
    return durs

def _ass_path_for_filter(p: Path) -> str:
    """Escapa la ruta para el filtro subtitles= de ffmpeg en Windows."""
    return str(p).replace("\\", "/").replace(":", "\\:")

def compose(clips: list[Path], voiceover: Path, ass: Path, scenes: list[dict],
            output: Path) -> bool:
    dur = _ffprobe_dur(voiceover)
    if dur <= 0 or not clips:
        print("    [COMPOSE] sin audio o sin clips"); return False
    durs = _scene_durations(scenes, dur, len(clips))

    cmd = ["ffmpeg", "-y"]
    for clip, d in zip(clips, durs):
        cmd += ["-stream_loop", "-1", "-t", f"{d:.3f}", "-i", str(clip)]
    cmd += ["-i", str(voiceover)]  # último input = audio

    parts, labels = [], ""
    for i in range(len(clips)):
        parts.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},setsar=1,fps={FPS},format=yuv420p,setpts=PTS-STARTPTS[v{i}]"
        )
        labels += f"[v{i}]"
    parts.append(f"{labels}concat=n={len(clips)}:v=1:a=0[vc]")
    parts.append(f"[vc]subtitles='{_ass_path_for_filter(ass)}'[vout]")
    filtergraph = ";".join(parts)

    cmd += [
        "-filter_complex", filtergraph,
        "-map", "[vout]", "-map", f"{len(clips)}:a",
        "-t", f"{dur:.3f}", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(output),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("    [FFMPEG ERROR]", r.stderr[-800:])
        return False
    return output.exists() and output.stat().st_size > 100_000


# ═══════════════════════════════════════════════════════════════════════════
# 6. QUALITY GATE (R13) — si UNO falla, el video NO se marca listo
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class QAResult:
    ok: bool = True
    checks: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)

def quality_gate(output: Path, ass: Path, clips: list[Path], voiceover: Path) -> QAResult:
    qa = QAResult()
    def check(name, cond, why):
        qa.checks[name] = bool(cond)
        if not cond:
            qa.ok = False; qa.reasons.append(why)

    # (a) subtítulos presentes (el .ass tiene eventos Dialogue)
    has_subs = ass.exists() and "Dialogue:" in ass.read_text(encoding="utf-8", errors="ignore")
    check("subtitulos_R11", has_subs, "Sin subtítulos hardcoded (R11)")
    # (b) b-roll temático único (R10): nunca menos de 3 escenas ni clips repetidos
    ids = [c.stem.split("_")[-1] for c in clips]
    check("broll_unico_R10", len(clips) >= 3 and len(set(ids)) == len(ids),
          f"B-roll insuficiente o repetido ({len(clips)} clips, {len(set(ids))} únicos)")
    # (c) duración video ≈ voiceover (sin freezes / sin cortar la voz)
    vd, ad = _ffprobe_dur(output), _ffprobe_dur(voiceover)
    check("duracion_ok", abs(vd - ad) <= 0.8, f"Desfase video/audio {vd:.2f}s vs {ad:.2f}s")
    # (d) resolución 9:16 + stream de audio
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(output)],
        capture_output=True, text=True).stdout.strip()
    check("formato_9x16", probe.replace("\n", "") in (f"{W},{H}", f"{W},{H},"),
          f"Resolución incorrecta: {probe}")
    a_probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(output)],
        capture_output=True, text=True).stdout.strip()
    check("tiene_audio", a_probe == "audio", "Sin pista de audio")
    return qa


# ═══════════════════════════════════════════════════════════════════════════
# ORQUESTADOR
# ═══════════════════════════════════════════════════════════════════════════
def _autosegment(voiceover_text: str, niche: str) -> list[dict]:
    """Si el guion no trae scenes: parte en frases y deriva query por keyword."""
    sentences = [s.strip() for s in re.split(r"(?<=[\.\?\!])\s+", voiceover_text) if s.strip()]
    return [{"text": s, "broll_query": _derive_query(s, niche)} for s in sentences]

def produce(script: dict, out_dir: Path, used_ids: set | None = None,
            voice_id: str | None = None) -> dict:
    vid = script.get("id", "VX")
    niche = script.get("niche", "curiosidades")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n{'='*64}\nPRODUCE {vid} — niche={niche}\n{'='*64}")

    # 1 + 2: gates de compliance y hook (pueden abortar)
    compliance_gate(script)
    hook_gate(script.get("hook", ""))
    print("  [GATE] compliance ✓  hook R16 ✓")

    # 3: voz única por video (R12)
    voiceover = out_dir / "voiceover.mp3"
    voice_used = _synthesize_voice(script["voiceover_text"], voiceover, vid, voice_id)

    # escenas (del guion o autosegmentadas)
    scenes = script.get("scenes") or _autosegment(script["voiceover_text"], niche)

    # 4: b-roll por escena + dedup global
    if used_ids is None:
        used_ids = _load_ledger()
    clips = fetch_scene_broll(scenes, niche, out_dir / "broll", used_ids)

    # 5: subtítulos whisper (R11) + compose
    print("  [SUBS] transcribiendo voiceover (whisper)...")
    words = transcribe_with_timestamps(voiceover)
    ass = out_dir / "subs.ass"
    ass.write_text(build_ass(group_chunks(words)), encoding="utf-8")
    final = out_dir / f"{vid}_final.mp4"
    composed = compose(clips, voiceover, ass, scenes, final)

    # 6: quality gate
    qa = quality_gate(final, ass, clips, voiceover) if composed else QAResult(ok=False, reasons=["compose falló"])
    _save_ledger(used_ids)

    status = "LISTO" if qa.ok else "RECHAZADO"
    print(f"  [QA] {status} — checks={qa.checks}")
    if not qa.ok:
        print(f"  [QA] razones: {qa.reasons}")
    # persistir caption/hashtags + reporte
    (out_dir / "caption_tiktok.txt").write_text(
        script.get("caption", "") + " " + " ".join(script.get("hashtags", [])),
        encoding="utf-8")
    report = {"id": vid, "niche": niche, "status": status, "voice": voice_used,
              "qa": asdict(qa), "scenes": len(scenes), "clips": len(clips),
              "final": str(final)}
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    return report


def produce_batch(scripts: list[dict], out_root: Path) -> list[dict]:
    """Produce un lote ROTANDO la voz round-robin (R12: ninguna voz consecutiva
    repetida) y compartiendo el ledger global de b-roll (R10: cero reciclaje)."""
    from scripts.autonomous.tts_elevenlabs import VOICE_POOL
    out_root = Path(out_root); out_root.mkdir(parents=True, exist_ok=True)
    used = _load_ledger()
    results = []
    for i, s in enumerate(scripts):
        vname, vid_voice = VOICE_POOL[i % len(VOICE_POOL)]  # round-robin = alternancia
        try:
            rep = produce(s, out_root / s["id"], used_ids=used, voice_id=vid_voice)
        except (ComplianceError, HookError) as e:
            rep = {"id": s.get("id"), "niche": s.get("niche"), "status": "RECHAZADO",
                   "voice": vname, "error": str(e)}
            print(f"  [GATE] {s.get('id')} RECHAZADO: {e}")
        results.append(rep)
        print(f"  → {s.get('id')}: {rep['status']}  (voz {rep.get('voice')})")
    _save_ledger(used)
    (out_root / "batch_report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results if r["status"] == "LISTO")
    print(f"\n[BATCH] {ok}/{len(results)} LISTO → {out_root}")
    return results


_DEMO_SCRIPT = {
    "id": "DEMO01",
    "niche": "cosmologia",
    "hook": "¿Qué pasaría si pudieras sostener una cucharada de estrella muerta?",
    "voiceover_text": (
        "¿Qué pasaría si pudieras sostener una cucharada de estrella muerta? "
        "Pesaría más que el monte Everest. Hablamos de una estrella de neutrones, "
        "el cadáver más denso del universo. Cuando una estrella gigante colapsa, "
        "aplasta sus átomos hasta que un dedal de su materia pesa mil millones de toneladas. "
        "Gira tan rápido que un segundo allí da cientos de vueltas. "
        "Sigue a CurioClip si quieres que tu cerebro explote una vez al día."
    ),
    "scenes": [
        {"text": "¿Qué pasaría si pudieras sostener una cucharada de estrella muerta?", "broll_query": "neutron star space"},
        {"text": "Pesaría más que el monte Everest.", "broll_query": "mount everest aerial"},
        {"text": "Hablamos de una estrella de neutrones, el cadáver más denso del universo.", "broll_query": "supernova explosion space"},
        {"text": "Cuando una estrella gigante colapsa, aplasta sus átomos.", "broll_query": "collapsing star animation"},
        {"text": "Un dedal de su materia pesa mil millones de toneladas.", "broll_query": "dense matter physics"},
        {"text": "Gira tan rápido que un segundo allí da cientos de vueltas.", "broll_query": "pulsar rotating space"},
        {"text": "Sigue a CurioClip para que tu cerebro explote una vez al día.", "broll_query": "galaxy stars night sky"},
    ],
    "caption": "El objeto más denso del universo cabe en una cuchara",
    "hashtags": ["#espacio", "#ciencia", "#universo", "#curioclip", "#fyp"],
}


def main():
    args = sys.argv[1:]
    if "--demo" in args:
        produce(_DEMO_SCRIPT, ROOT / "output_pipeline_v2" / "DEMO01")
    elif "--script" in args:
        sp = Path(args[args.index("--script") + 1])
        script = json.loads(sp.read_text(encoding="utf-8"))
        out = args[args.index("--out") + 1] if "--out" in args else f"output_pipeline_v2/{script.get('id','VX')}"
        produce(script, ROOT / out)
    elif "--batch" in args:
        sp = Path(args[args.index("--batch") + 1])
        scripts = json.loads(sp.read_text(encoding="utf-8"))
        out = args[args.index("--out") + 1] if "--out" in args else "output_pipeline_v2/batch"
        produce_batch(scripts, ROOT / out)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
