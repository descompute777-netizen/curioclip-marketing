#!/usr/bin/env python3
"""Recompose BATCH_CLONE_01 with real Pexels B-roll video + AI images as accents."""
import subprocess, json, sys, os, time, shutil, random
import urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / "obsidian_vault" / "30_Contenido" / "BATCH_CLONE_01"
PEXELS_KEY = "k0iMZlUKh9p7jpNUKjRQQ4eCPcXQ7YW4ufpBkEoZOCbKuDOt9x3xVqjR"
FPS = 30
W, H = 1080, 1920

BROLL_QUERIES = {
    "VC1": [
        "ancient greek temple", "hospital surgery", "ancient greece columns",
        "doctor medicine", "ancient ruins sunset", "healing ritual",
        "greek statue dramatic", "candle dark room"
    ],
    "VC2": [
        "roman bath ancient", "soap water bubbles", "medieval castle dark",
        "dirty hands washing", "shower water clean", "ancient egypt pyramid",
        "french palace interior", "hygiene bathroom modern"
    ],
    "VC3": [
        "tired exhausted person", "insomnia dark room", "brain neural scan",
        "coffee cup desk night", "hallucination abstract", "clock ticking time",
        "hospital emergency red", "eye close up fatigue"
    ],
    "VC4": [
        "thermometer temperature", "ice frozen extreme cold", "desert heat sun",
        "fire flames close up", "snow blizzard storm", "human body science",
        "fever sick person", "cold breath winter"
    ],
    "VC5": [
        "teeth dental close up", "ancient artifact tool", "medieval dark room",
        "toothbrush modern clean", "roman architecture bath", "pain face expression",
        "dentist operation", "smile white teeth"
    ],
}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def get_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(r.stdout)["format"]["duration"])


def search_pexels(query, per_page=3):
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
            else:
                if vid.get("video_files"):
                    results.append(vid["video_files"][0]["link"])
        return results
    except Exception as e:
        print(f"    [WARN] Pexels '{query}': {e}")
        return []


def download(url, dest):
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
        print(f"    [WARN] download: {e}")
        return False


def fetch_broll(vc_name):
    """Download B-roll clips for a VC. Returns list of video paths."""
    queries = BROLL_QUERIES.get(vc_name, ["science", "dark abstract", "nature dramatic"])
    broll_dir = BATCH / vc_name / "broll"
    broll_dir.mkdir(exist_ok=True)

    clips = []
    idx = 0
    for query in queries:
        print(f"  Pexels: '{query}'")
        urls = search_pexels(query, per_page=2)
        for url in urls[:1]:
            dest = broll_dir / f"clip_{idx:02d}.mp4"
            if download(url, dest):
                clips.append(dest)
                idx += 1
        time.sleep(0.3)

    print(f"  -> {len(clips)} B-roll clips downloaded")
    return clips


def make_image_segment(img, out, duration):
    """Create a short dynamic segment from AI image (quick zoom burst)."""
    frames = int(duration * FPS)
    zp = (f"zoompan=z='if(eq(on\\,0)\\,1.0\\,min(zoom+0.004\\,1.3))':"
          f"d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"s={W}x{H}:fps={FPS}")
    # Pre-scale image for zoompan
    zpw, zph = int(W * 1.35), int(H * 1.35)
    prep = out.parent / f"_prep_{out.stem}.jpg"
    run(["ffmpeg", "-y", "-i", str(img),
         "-vf", f"scale={zpw}:{zph}:force_original_aspect_ratio=increase,crop={zpw}:{zph}",
         "-q:v", "2", str(prep)])

    run(["ffmpeg", "-y", "-loop", "1", "-i", str(prep),
         "-vf", zp,
         "-t", str(duration),
         "-c:v", "libx264", "-preset", "fast", "-crf", "20",
         "-pix_fmt", "yuv420p", str(out)])
    prep.unlink(missing_ok=True)
    return out.exists() and out.stat().st_size > 1000


def make_broll_segment(clip, out, duration):
    """Trim and scale a B-roll video clip to exact duration and 9:16."""
    try:
        clip_dur = get_duration(clip)
    except Exception:
        clip_dur = 10.0

    # Random start point for variety
    max_start = max(0, clip_dur - duration - 0.5)
    ss = random.uniform(0, max_start) if max_start > 0 else 0

    run(["ffmpeg", "-y", "-ss", f"{ss:.2f}", "-i", str(clip),
         "-t", str(duration),
         "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1",
         "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])
    return out.exists() and out.stat().st_size > 1000


def compose_vc(vc_name):
    vc = BATCH / vc_name
    audio = vc / "voiceover.mp3"
    subs = vc / "subtitles.ass"
    final = vc / "final_video.mp4"

    if not audio.exists():
        print(f"[SKIP] {vc_name}: missing voiceover")
        return False

    dur = get_duration(audio)
    print(f"\n{'='*60}")
    print(f"[{vc_name}] Total duration: {dur:.1f}s")
    print(f"{'='*60}")

    # 1) Fetch B-roll videos
    broll_clips = fetch_broll(vc_name)
    if len(broll_clips) < 3:
        print(f"  [ERROR] Only {len(broll_clips)} B-roll clips, need at least 3")
        return False

    # 2) Get AI images
    ai_images = sorted(vc.glob("scene_*.jpg"))
    print(f"  AI images: {len(ai_images)}")

    # 3) Plan the edit: alternate B-roll (4-6s) with AI image accents (2-3s)
    segments = []
    seg_dir = vc / "_segments"
    seg_dir.mkdir(exist_ok=True)

    n_broll = len(broll_clips)
    n_ai = len(ai_images)

    # Build segment timeline
    # Pattern: broll(5s) -> broll(4s) -> AI(2.5s) -> broll(5s) -> broll(4s) -> AI(2.5s) -> ...
    timeline = []
    broll_idx = 0
    ai_idx = 0
    remaining = dur

    while remaining > 0:
        # 2 B-roll clips
        for _ in range(2):
            if remaining <= 0:
                break
            d = min(random.uniform(4.0, 6.0), remaining)
            timeline.append(("broll", broll_idx % n_broll, d))
            broll_idx += 1
            remaining -= d

        # 1 AI image accent (if available)
        if remaining > 0 and n_ai > 0:
            d = min(random.uniform(2.0, 3.0), remaining)
            timeline.append(("ai", ai_idx % n_ai, d))
            ai_idx += 1
            remaining -= d

    print(f"  Timeline: {len(timeline)} segments ({sum(t[2] for t in timeline):.1f}s)")

    # 4) Create each segment
    seg_paths = []
    for i, (stype, idx, sdur) in enumerate(timeline):
        seg_out = seg_dir / f"seg_{i:03d}.mp4"
        if stype == "broll":
            clip = broll_clips[idx]
            ok = make_broll_segment(clip, seg_out, sdur)
        else:
            img = ai_images[idx]
            ok = make_image_segment(img, seg_out, sdur)

        if ok:
            seg_paths.append(seg_out)
        else:
            print(f"    [WARN] segment {i} failed, skipping")

    if not seg_paths:
        print(f"  [ERROR] No segments created")
        return False

    # 5) Concat all segments
    concat_txt = vc / "_concat2.txt"
    with open(concat_txt, "w") as f:
        for s in seg_paths:
            f.write(f"file '{s}'\n")

    concat_mp4 = vc / "_concat2.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_txt), "-c", "copy", str(concat_mp4)])

    # 6) Add audio + subtitles
    temp_subs = vc / "_subs2.ass"
    shutil.copy2(subs, temp_subs)

    r = run([
        "ffmpeg", "-y",
        "-i", concat_mp4.name,
        "-i", "voiceover.mp3",
        "-vf", "ass=_subs2.ass",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-pix_fmt", "yuv420p",
        "final_video.mp4"
    ], cwd=str(vc))

    # 7) Cleanup
    for s in seg_paths:
        s.unlink(missing_ok=True)
    concat_txt.unlink(missing_ok=True)
    concat_mp4.unlink(missing_ok=True)
    temp_subs.unlink(missing_ok=True)
    shutil.rmtree(seg_dir, ignore_errors=True)

    if final.exists() and final.stat().st_size > 500_000:
        mb = final.stat().st_size / 1048576
        print(f"  [OK] {vc_name}/final_video.mp4 — {mb:.1f} MB")
        return True

    print(f"  [FAIL] {vc_name}")
    return False


if __name__ == "__main__":
    targets = sys.argv[1:] or ["VC1", "VC2", "VC3", "VC4", "VC5"]
    ok = fail = 0
    for t in targets:
        if compose_vc(t):
            ok += 1
        else:
            fail += 1
    print(f"\n{'='*60}")
    print(f"RESULTS: {ok} OK, {fail} FAIL")
    print(f"{'='*60}")
