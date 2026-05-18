"""Produce V5/V6/V7 en secuencia."""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
sys.path.insert(0, str(ROOT))

from src.pipeline.auto_editor_generic import produce_video
from configs.v5_tunguska   import VIDEO_CONFIG as V5
from configs.v6_conan      import VIDEO_CONFIG as V6
from configs.v7_cosquillas import VIDEO_CONFIG as V7

VIDEOS = [V5, V6, V7]

if __name__ == "__main__":
    results = {}
    t0 = time.time()
    for cfg in VIDEOS:
        vid = cfg["video_id"]
        print(f"\n{'#'*60}\n# PRODUCIENDO {vid}\n{'#'*60}")
        try:
            out = produce_video(cfg)
            results[vid] = str(out) if out else "FAIL"
        except Exception as e:
            print(f"[ERROR] {vid}: {e}")
            import traceback; traceback.print_exc()
            results[vid] = f"ERROR: {e}"

    elapsed = time.time() - t0
    print(f"\n{'='*60}\nDONE en {elapsed:.0f}s\n{'='*60}")
    for v, s in results.items():
        icon = "OK" if "FAIL" not in s and "ERROR" not in s else "FAIL"
        print(f"  [{icon}] {v}: {s}")
