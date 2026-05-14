"""
Produce todos los videos V1-V4 en secuencia usando auto_editor_generic.
Uso: python -m src.pipeline.produce_all
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import time

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
sys.path.insert(0, str(ROOT))

from src.pipeline.auto_editor_generic import produce_video
from configs.v1_medusa   import VIDEO_CONFIG as V1_CFG
from configs.v2_bacterias import VIDEO_CONFIG as V2_CFG
from configs.v3_radio     import VIDEO_CONFIG as V3_CFG
from configs.v4_leyes     import VIDEO_CONFIG as V4_CFG

VIDEOS = [V2_CFG, V1_CFG, V3_CFG, V4_CFG]  # orden de publicación sprint 2

if __name__ == "__main__":
    results = {}
    start = time.time()

    for cfg in VIDEOS:
        vid_id = cfg["video_id"]
        print(f"\n{'#'*60}")
        print(f"# PRODUCIENDO {vid_id}...")
        print(f"{'#'*60}")
        try:
            result = produce_video(cfg)
            results[vid_id] = "OK" if result else "FAIL"
        except Exception as e:
            print(f"[ERROR] {vid_id}: {e}")
            results[vid_id] = f"ERROR: {e}"

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"PRODUCCIÓN COMPLETADA en {elapsed:.0f}s")
    print(f"{'='*60}")
    for vid, status in results.items():
        icon = "✅" if status == "OK" else "❌"
        print(f"  {icon} {vid}: {status}")
    print()
    print("Próximo paso:")
    print("  1. Revisar videos en obsidian_vault/SEMANAS/SEMANA_02_*/*/OUTPUT/")
    print("  2. Ejecutar: python -m src.bridge.chrome_bridge launch")
    print("  3. Subir cada video a TikTok Studio con publish_v5.py (adaptar ruta)")
