"""
TRIBE v2 MCP Server Wrapper
============================
Expone TRIBE v2 (Meta FAIR) como servidor MCP.
Tools: predict_neural_response, compare_variants, get_attention_heatmap
"""

import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

_model = None

def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        from tribev2 import TribeModel
        cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "cache", "tribe")
        os.makedirs(cache_dir, exist_ok=True)
        _model = TribeModel.from_pretrained("facebook/tribev2", cache_folder=cache_dir)
        return _model
    except ImportError:
        raise RuntimeError("tribev2 no instalado. Ejecuta: pip install tribev2")


def predict_neural_response(video_path: str, analysis_type: str = "full") -> dict:
    """Predice respuesta neurocognitiva para un video."""
    if not os.path.exists(video_path):
        return {"error": f"Video no encontrado: {video_path}"}
    model = _load_model()
    df = model.get_events_dataframe(video_path=video_path)
    preds, segments = model.predict(events=df)
    n_ts = preds.shape[0]

    attention = [round(max(0, min(10, float(preds[t].mean()) * 10)), 2) for t in range(n_ts)]
    avg = sum(attention) / max(len(attention), 1)
    weak = [round(float(i), 1) for i, s in enumerate(attention) if s < avg * 0.7]
    nci = round(avg, 2)
    high = sum(1 for s in attention if s > 5.0)
    retention = round((high / max(len(attention), 1)) * 100, 1)

    result = {"nci_score": nci, "retention_prediction": retention,
              "weak_points": weak, "video_duration_seconds": n_ts}
    if analysis_type in ("full", "attention_only"):
        result["attention_heatmap"] = attention
    if analysis_type in ("full", "emotion_only"):
        result["emotion_trajectory"] = [
            round(max(0, min(10, float(preds[t].std()) * 5)), 2) for t in range(n_ts)]
    return result


def compare_variants(video_paths: list) -> dict:
    """Compara 2-5 variantes de video."""
    results = []
    for p in video_paths:
        a = predict_neural_response(p, "attention_only")
        if "error" in a:
            continue
        results.append({"video": os.path.basename(p), "nci": a["nci_score"],
                        "retention": a["retention_prediction"]})
    results.sort(key=lambda x: x["nci"], reverse=True)
    return {"ranking": results, "winner": results[0]["video"] if results else "N/A"}


if __name__ == "__main__":
    print("[INFO] TRIBE v2 MCP Server — Listo para integración")
