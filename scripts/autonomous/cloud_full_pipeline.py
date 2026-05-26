#!/usr/bin/env python3
"""
Cloud Full Pipeline — Producción 100% Autónoma
================================================
Corre en GitHub Actions (Ubuntu). Sin PC local.

Pipeline completo por video:
  1. Lee guion del schedule.json
  2. edge-tts → voiceover MP3 (gratis)
  3. whisper → subtitulos ASS word-level (gratis)
  4. Pexels API → 8+ B-roll clips temáticos (gratis)
  5. ffmpeg → composición 9:16 1080x1920 con:
     - B-roll video real (cortes rápidos 4-6s)
     - AI images como acentos (si existen en repo)
     - Subtitulos ASS hardcoded
     - Voiceover audio
  6. Output → SEMANA_XX/DIA/OUTPUT/video_final.mp4
  7. upload_release.py sube a GitHub Releases

Deps: pip install edge-tts openai-whisper requests
System: ffmpeg (pre-installed on Ubuntu runners)
Secrets: PEXELS_API_KEY, GEMINI_API_KEY
"""
import os, sys, json, subprocess, datetime, random, time, shutil, tempfile
import urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VAULT = ROOT / "obsidian_vault"
SEMANAS = VAULT / "SEMANAS"
SPRINT_N = ((datetime.date.today() - datetime.date(2026, 5, 6)).days // 7) + 1
TODAY = datetime.date.today().isoformat()
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")
FPS = 30
W, H = 1080, 1920

BROLL_QUERIES = {
    "misterio":    ["abandoned building dark", "mystery fog night", "dark corridor cinematic"],
    "ciencia":     ["science laboratory", "brain neural scan", "microscope cells"],
    "historia":    ["ancient ruins temple", "medieval castle", "old map document"],
    "psicologia":  ["human brain close up", "eye pupil close up", "shadow silhouette"],
    "cosmologia":  ["galaxy space stars", "milky way timelapse", "earth orbit"],
    "salud":       ["hospital corridor", "heartbeat monitor", "medicine pills"],
    "tecnologia":  ["circuit board close up", "smartphone screen", "robot arm"],
    "cuerpo":      ["anatomy skeleton", "blood cells", "muscle movement"],
    "default":     ["dark cinematic abstract", "particles floating", "dramatic lighting"],
}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=kw.pop("timeout", 120), **kw)


def get_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(r.stdout)["format"]["duration"])


def detect_subniche(text):
    t = text.lower()
    if any(w in t for w in ["misterio", "señal", "desapareci", "inexplicable"]): return "misterio"
    if any(w in t for w in ["cerebro", "dormir", "psicolog", "mental"]): return "psicologia"
    if any(w in t for w in ["temperat", "cuerpo", "organo", "sangre"]): return "cuerpo"
    if any(w in t for w in ["hospital", "medic", "bacteria", "virus"]): return "salud"
    if any(w in t for w in ["napoleon", "guerra", "histori", "medieval", "antiguo", "grecia", "roma"]): return "historia"
    if any(w in t for w in ["galaxia", "sol", "universo", "luna", "espacio"]): return "cosmologia"
    if any(w in t for w in ["telefono", "smartphone", "tecnolog", "internet"]): return "tecnologia"
    if any(w in t for w in ["fisica", "quimica", "ciencia", "experiment"]): return "ciencia"
    return "default"


def pick_voice(guion_id):
    voices = [
        ("es-MX-JorgeNeural", "+12%"), ("es-AR-TomasNeural", "+10%"),
        ("es-CO-GonzaloNeural", "+11%"), ("es-CL-LorenzoNeural", "+10%"),
        ("es-MX-DaliaNeural", "+8%"), ("es-ES-AlvaroNeural", "+10%"),
        ("es-VE-SebastianNeural", "+12%"), ("es-PE-AlexNeural", "+10%"),
        ("es-CU-ManuelNeural", "+11%"), ("es-EC-LuisNeural", "+10%"),
    ]
    idx = hash(guion_id or "default") % len(voices)
    return voices[idx]


# ─── TTS ─────────────────────────────────────────────────────────────────

def generate_voiceover(text, output, guion_id=None):
    voice, rate = pick_voice(guion_id)
    r = run([sys.executable, "-m", "edge_tts", "--voice", voice, "--rate", rate,
             "--text", text[:3000], "--write-media", str(output)], timeout=60)
    ok = r.returncode == 0 and output.exists() and output.stat().st_size > 1000
    if ok:
        print(f"  [TTS] {voice} {rate} → {output.stat().st_size//1024}KB")
    else:
        print(f"  [TTS FAIL] {r.stderr[:200]}")
    return ok


# ─── SUBTITLES ───────────────────────────────────────────────────────────

def generate_subtitles(audio_path, output_ass):
    """Generate word-level ASS subtitles via whisper."""
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path), language="es", word_timestamps=True)

        lines = [
            "[Script Info]", f"Title: {audio_path.stem}",
            "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,Arial Black,58,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,2,40,40,200,1",
            "Style: Highlight,Arial Black,58,&H0000D4FF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,2,40,40,200,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]

        def fmt(t):
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            cs = int((t % 1) * 100)
            return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

        for seg in result.get("segments", []):
            words = seg.get("words", [])
            if words:
                for w in words:
                    lines.append(f"Dialogue: 0,{fmt(w['start'])},{fmt(w['end'])},Highlight,,0,0,0,,{w['word'].strip()}")
            else:
                lines.append(f"Dialogue: 0,{fmt(seg['start'])},{fmt(seg['end'])},Highlight,,0,0,0,,{seg['text'].strip()}")

        output_ass.write_text("\n".join(lines), encoding="utf-8")
        print(f"  [SUBS] {output_ass.name} ({output_ass.stat().st_size//1024}KB)")
        return True
    except Exception as e:
        print(f"  [SUBS FAIL] {e}")
        return False


# ─── PEXELS B-ROLL ───────────────────────────────────────────────────────

def search_pexels(query, per_page=2):
    if not PEXELS_KEY:
        return []
    q = urllib.parse.quote_plus(query)
    url = f"https://api.pexels.com/videos/search?query={q}&per_page={per_page}&orientation=portrait"
    req = urllib.request.Request(url, headers={
        "Authorization": PEXELS_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        results = []
        for vid in data.get("videos", []):
            for vf in vid.get("video_files", []):
                if vf.get("height", 0) >= 720:
                    results.append(vf["link"])
                    break
        return results
    except Exception as e:
        print(f"    [WARN] Pexels '{query}': {e}")
        return []


def download_file(url, dest):
    if dest.exists() and dest.stat().st_size > 10000:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            with open(dest, "wb") as f:
                while chunk := r.read(65536):
                    f.write(chunk)
        return dest.stat().st_size > 10000
    except Exception as e:
        print(f"    [DL FAIL] {e}")
        return False


def fetch_broll(queries, broll_dir):
    broll_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    idx = 0
    for query in queries:
        urls = search_pexels(query, per_page=2)
        for url in urls[:1]:
            dest = broll_dir / f"clip_{idx:02d}.mp4"
            if download_file(url, dest):
                clips.append(dest)
                idx += 1
        time.sleep(0.3)
    print(f"  [BROLL] {len(clips)} clips from Pexels")
    return clips


# ─── VIDEO COMPOSITION ───────────────────────────────────────────────────

def make_broll_segment(clip, out, duration):
    try:
        clip_dur = get_duration(clip)
    except Exception:
        clip_dur = 10.0
    max_start = max(0, clip_dur - duration - 0.5)
    ss = random.uniform(0, max_start) if max_start > 0 else 0
    run(["ffmpeg", "-y", "-ss", f"{ss:.2f}", "-i", str(clip),
         "-t", str(duration),
         "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1",
         "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "22",
         "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])
    return out.exists() and out.stat().st_size > 1000


def make_image_segment(img, out, duration):
    frames = int(duration * FPS)
    zpw, zph = int(W * 1.35), int(H * 1.35)
    prep = out.parent / f"_prep_{out.stem}.jpg"
    run(["ffmpeg", "-y", "-i", str(img),
         "-vf", f"scale={zpw}:{zph}:force_original_aspect_ratio=increase,crop={zpw}:{zph}",
         "-q:v", "2", str(prep)])
    zp = (f"zoompan=z='if(eq(on\\,0)\\,1.0\\,min(zoom+0.004\\,1.3))':"
          f"d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"s={W}x{H}:fps={FPS}")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(prep), "-vf", zp,
         "-t", str(duration), "-c:v", "libx264", "-preset", "fast", "-crf", "22",
         "-pix_fmt", "yuv420p", str(out)])
    prep.unlink(missing_ok=True)
    return out.exists() and out.stat().st_size > 1000


def compose_full_video(broll_clips, ai_images, voiceover, subs_ass, output):
    """Compose final video: B-roll + AI accents + voiceover + subtitles."""
    dur = get_duration(voiceover)
    n_broll = len(broll_clips)
    n_ai = len(ai_images)

    if n_broll == 0:
        print("  [ERROR] No B-roll clips")
        return False

    seg_dir = output.parent / "_segments"
    seg_dir.mkdir(exist_ok=True)

    # Build timeline: broll(4-6s) x2 → ai_accent(2-3s) → repeat
    timeline = []
    broll_idx = ai_idx = 0
    remaining = dur

    while remaining > 0:
        for _ in range(2):
            if remaining <= 0: break
            d = min(random.uniform(4.0, 6.0), remaining)
            timeline.append(("broll", broll_idx % n_broll, d))
            broll_idx += 1
            remaining -= d
        if remaining > 0 and n_ai > 0:
            d = min(random.uniform(2.0, 3.0), remaining)
            timeline.append(("ai", ai_idx % n_ai, d))
            ai_idx += 1
            remaining -= d

    print(f"  [TIMELINE] {len(timeline)} segments ({sum(t[2] for t in timeline):.1f}s)")

    # Create segments
    seg_paths = []
    for i, (stype, idx, sdur) in enumerate(timeline):
        seg_out = seg_dir / f"seg_{i:03d}.mp4"
        if stype == "broll":
            ok = make_broll_segment(broll_clips[idx], seg_out, sdur)
        else:
            ok = make_image_segment(ai_images[idx], seg_out, sdur)
        if ok:
            seg_paths.append(seg_out)

    if not seg_paths:
        print("  [ERROR] No segments created")
        return False

    # Concat segments
    concat_txt = output.parent / "_concat.txt"
    with open(concat_txt, "w") as f:
        for s in seg_paths:
            f.write(f"file '{s}'\n")

    concat_mp4 = output.parent / "_concat.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_txt), "-c", "copy", str(concat_mp4)])

    # Add audio + subtitles
    subs_copy = output.parent / "_subs.ass"
    shutil.copy2(subs_ass, subs_copy)

    # Platform-aware subtitle path
    if sys.platform == "win32":
        subs_arg = f"ass='{str(subs_copy).replace(chr(92), '/').replace(':', chr(92)+chr(92)+':')}'"
    else:
        subs_arg = f"ass={subs_copy}"

    run(["ffmpeg", "-y",
         "-i", str(concat_mp4), "-i", str(voiceover),
         "-vf", subs_arg,
         "-c:v", "libx264", "-preset", "fast", "-crf", "22",
         "-c:a", "aac", "-b:a", "128k",
         "-shortest", "-pix_fmt", "yuv420p", str(output)], timeout=300)

    # Cleanup
    for s in seg_paths: s.unlink(missing_ok=True)
    concat_txt.unlink(missing_ok=True)
    concat_mp4.unlink(missing_ok=True)
    subs_copy.unlink(missing_ok=True)
    shutil.rmtree(seg_dir, ignore_errors=True)

    if output.exists() and output.stat().st_size > 500_000:
        mb = output.stat().st_size / 1048576
        print(f"  [OK] {output.name} — {mb:.1f} MB")
        return True
    print(f"  [FAIL] output missing or too small")
    return False


# ─── MAIN PIPELINE ───────────────────────────────────────────────────────

def produce_one(guion_id, voiceover_text, caption, out_dir, ai_images_dir=None):
    """Produce one complete video from scratch."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_tmp"
    tmp.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"[PRODUCE] {guion_id}")
    print(f"{'='*60}")

    # 1) Voiceover
    vo = out_dir / "voiceover.mp3"
    if not (vo.exists() and vo.stat().st_size > 1000):
        if not generate_voiceover(voiceover_text, vo, guion_id):
            return None

    # 2) Subtitles
    subs = out_dir / "subtitles.ass"
    if not (subs.exists() and subs.stat().st_size > 500):
        if not generate_subtitles(vo, subs):
            return None

    # 3) B-roll
    subniche = detect_subniche(voiceover_text)
    queries = BROLL_QUERIES.get(subniche, BROLL_QUERIES["default"])
    extra = detect_subniche(caption)
    if extra != subniche:
        queries = queries + BROLL_QUERIES.get(extra, [])
    broll_clips = fetch_broll(queries[:8], tmp / "broll")

    # 4) AI images (if available in repo)
    ai_images = []
    if ai_images_dir and ai_images_dir.exists():
        ai_images = sorted(ai_images_dir.glob("scene_*.jpg")) + sorted(ai_images_dir.glob("scene_*.png"))
        print(f"  [AI] {len(ai_images)} images found")

    if not broll_clips and not ai_images:
        print("  [ERROR] No visual content available")
        return None

    # 5) Compose
    final = out_dir / f"{guion_id}_final.mp4"
    ok = compose_full_video(broll_clips, ai_images, vo, subs, final)

    # Cleanup tmp
    shutil.rmtree(tmp, ignore_errors=True)

    return final if ok else None


def main():
    """Read schedule.json and produce all pending videos."""
    print(f"\n{'#'*60}")
    print(f"# CLOUD FULL PIPELINE — Sprint {SPRINT_N} — {TODAY}")
    print(f"{'#'*60}")

    # Find schedule
    pub_dir = VAULT / "40_Publicacion"
    sched_files = sorted(pub_dir.glob("schedule_sprint*.json"), reverse=True)
    if not sched_files:
        print("[SKIP] No schedule found. Run weekly_sprint.py first.")
        return

    sched_path = sched_files[0]
    schedule = json.loads(sched_path.read_text(encoding="utf-8"))
    sprint = schedule.get("sprint", SPRINT_N)
    week_start = schedule.get("week_start", TODAY)
    print(f"[SCHED] {sched_path.name} | Sprint {sprint}")

    semana_dir = SEMANAS / f"SEMANA_{sprint:02d}_{week_start}_auto"
    produced = 0

    for video in schedule.get("videos", []):
        if video.get("video_url"):
            print(f"  [SKIP] {video['guion_id']} — already has URL")
            continue

        guion_id = video["guion_id"]
        day = video.get("day", "lunes").upper()
        vo_text = video.get("voiceover_text") or video.get("caption", "")
        caption = video.get("caption", "")

        day_dir = semana_dir / day / "OUTPUT"
        ai_dir = VAULT / "30_Contenido" / guion_id  # if AI images exist per guion

        result = produce_one(guion_id, vo_text, caption, day_dir, ai_dir)
        if result:
            video["local_video_path"] = str(result)
            produced += 1

    # Update schedule
    sched_path.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'#'*60}")
    print(f"# DONE: {produced} videos produced")
    print(f"{'#'*60}")


if __name__ == "__main__":
    main()
