#!/usr/bin/env python3
"""Compose BATCH_CLONE_01 videos: AI images + voiceover + subtitles -> final MP4 9:16."""
import subprocess, json, sys, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / "obsidian_vault" / "30_Contenido" / "BATCH_CLONE_01"
FPS = 30
OUT_W, OUT_H = 1080, 1920
ZP_W, ZP_H = int(OUT_W * 1.25), int(OUT_H * 1.25)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0 and r.stderr:
        print(f"    stderr: {r.stderr[:300]}")
    return r


def get_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(r.stdout)["format"]["duration"])


def prep_image(src, dst):
    run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", f"scale={ZP_W}:{ZP_H}:force_original_aspect_ratio=increase,crop={ZP_W}:{ZP_H}",
        "-q:v", "2",
        str(dst)
    ])


def make_segment(img, out, duration, effect_idx):
    frames = int(duration * FPS)
    effects = [
        f"z='if(eq(on\\,0)\\,1.0\\,min(zoom+0.0008\\,1.18))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        f"z='if(eq(on\\,0)\\,1.18\\,max(zoom-0.0008\\,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        f"z=1.08:x='iw/2-(iw/zoom/2)':y='min(ih*0.02+on*0.35\\,ih-ih/zoom)'",
    ]
    e = effects[effect_idx % len(effects)]
    zp = f"zoompan={e}:d={frames}:s={OUT_W}x{OUT_H}:fps={FPS}"

    run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(img),
        "-vf", zp,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        str(out)
    ])


def compose_vc(vc_name):
    vc = BATCH / vc_name
    audio = vc / "voiceover.mp3"
    subs = vc / "subtitles.ass"
    final = vc / "final_video.mp4"

    if final.exists() and final.stat().st_size > 500_000:
        mb = final.stat().st_size / 1048576
        print(f"[SKIP] {vc_name}: final_video.mp4 already exists ({mb:.1f} MB)")
        return True

    if not audio.exists():
        print(f"[SKIP] {vc_name}: missing voiceover")
        return False

    images = sorted(vc.glob("scene_*.jpg"))
    if not images:
        print(f"[SKIP] {vc_name}: no images")
        return False

    dur = get_duration(audio)
    n = len(images)
    seg_dur = dur / n
    print(f"\n{'='*50}")
    print(f"[{vc_name}] {n} images x {seg_dur:.1f}s = {dur:.1f}s")
    print(f"{'='*50}")

    # 1) Pre-process images to 9:16 at zoompan resolution
    prep_dir = vc / "_prep"
    prep_dir.mkdir(exist_ok=True)
    for img in images:
        dst = prep_dir / img.name
        if not dst.exists() or dst.stat().st_size < 1000:
            print(f"  Prep: {img.name}")
            prep_image(img, dst)

    # 2) Ken Burns segments
    segments = []
    for i, img in enumerate(images):
        seg = vc / f"_seg{i:02d}.mp4"
        prep = prep_dir / img.name
        if not prep.exists():
            print(f"  [ERROR] prep missing: {prep}")
            return False
        print(f"  Segment {i+1}/{n}: {img.name} (effect {i%3})")
        make_segment(prep, seg, seg_dur, i)
        if seg.exists() and seg.stat().st_size > 1000:
            segments.append(seg)
        else:
            print(f"  [ERROR] segment failed: {seg}")
            return False

    # 3) Concatenate segments
    concat_txt = vc / "_concat.txt"
    with open(concat_txt, "w") as f:
        for s in segments:
            f.write(f"file '{s.name}'\n")

    concat_mp4 = vc / "_concat.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_txt), "-c", "copy", str(concat_mp4)])

    # 4) Add audio + burn subtitles -> final
    # Copy subs to vc dir with simple name to avoid Windows path issues
    temp_subs = vc / "_subs.ass"
    shutil.copy2(subs, temp_subs)

    r = run([
        "ffmpeg", "-y",
        "-i", concat_mp4.name,
        "-i", "voiceover.mp3",
        "-vf", f"ass=_subs.ass",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-pix_fmt", "yuv420p",
        "final_video.mp4"
    ], cwd=str(vc))

    # 5) Cleanup temp files
    for s in segments:
        s.unlink(missing_ok=True)
    concat_txt.unlink(missing_ok=True)
    concat_mp4.unlink(missing_ok=True)
    temp_subs.unlink(missing_ok=True)
    shutil.rmtree(prep_dir, ignore_errors=True)

    if final.exists() and final.stat().st_size > 100_000:
        mb = final.stat().st_size / 1048576
        print(f"  [OK] {vc_name}/final_video.mp4 — {mb:.1f} MB")
        return True

    print(f"  [FAIL] {vc_name} — output missing or too small")
    return False


if __name__ == "__main__":
    targets = sys.argv[1:] or ["VC1", "VC2", "VC3", "VC4", "VC5"]
    ok = fail = 0
    for t in targets:
        if compose_vc(t):
            ok += 1
        else:
            fail += 1
    print(f"\n{'='*50}")
    print(f"RESULTS: {ok} OK, {fail} FAIL")
    print(f"{'='*50}")
